from pathlib import PurePosixPath
from ebooklib import epub
from bs4 import BeautifulSoup
import regex as re
import os
import uuid
from flask_socketio import SocketIO
from gandy.full_pipelines.base_pipeline import BasePipeline
from gandy.state.context_state import ContextState
from gandy.state.config_state import config_state
from gandy.utils.text_processing import add_seps
from gandy.utils.fancy_logger import logger
from io import BytesIO
from PIL import Image

# See: https://docs.python.org/3/library/os.path.html#os.path.expanduser
save_folder_path = os.path.expanduser("~/Documents/Mango/books")


def make_folder(folder_path: str):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)


class DataCleaner:
    def __init__(self):
        pass

    @classmethod
    def replace_many(self, sentences):
        return sentences  # Use to clean_text_v2 here.

    @classmethod
    def strip_html(self, sentences):
        def _rem_newl(l):
            return BeautifulSoup(l, features="html.parser").get_text()

        return [_rem_newl(l) for l in sentences]


def emit_progress(socketio: SocketIO, j, sentences_len: int):
    data = {
        "progressFrac": max(j / max(sentences_len, 1), 0.01),
        "sentsTotal": sentences_len,
        "sentsDone": j,
    }
    socketio.patched_emit("progress_epub", data)


sent_regex = re.compile(r"([.?!])([a-zA-Z0-9_])")


def translate_one_sentence(
    t: str, app_pipeline: BasePipeline, context_state: ContextState
):
    t_o: str = DataCleaner.replace_many(DataCleaner.strip_html([t]))[0].strip()
    if len(t_o) == 0:
        return t

    # Create input.
    t = add_seps(context_state.prev_source_text_list + [t_o])

    (
        translated_text,
        processed_source_text,
    ) = app_pipeline.text_to_text(
        t,
        return_source_text=True,
    )
    translated_text = translated_text[
        0
    ]  # Batch of 1. Only get the sentence string itself.

    # Because EPUBs are weird, sometimes the output text will have multiple sentences with poor spacing. Quick hack.
    translated_text = re.sub(sent_regex, r"\1 \2", translated_text)

    context_state.update_source_list(
        processed_source_text[0],
        config_state.n_context,
    )
    # Add current sentence to contextual outputs for future sentences.
    context_state.update_target_list(
        translated_text,
        config_state.n_context,
    )

    return translated_text

def translate_img(app_pipeline: BasePipeline, img: Image.Image):
    def dummy_fn(*args, **kwargs):
        pass

    # Note context_state is not used here - image tasks are "closed" - they only remember and use context within that image.
    new_image, is_amg = app_pipeline.image_to_image(
        img, progress_cb=dummy_fn, cb_on_text_done=dummy_fn,
    )

    return new_image

# Vibe coded util.
def _resolve_epub_href(doc_href: str, src: str) -> str:
    """
    Resolve an <img src="..."> against the containing HTML item's href.
    EPUB uses posix paths.
    Handles cases where doc_href is None by assuming src is relative to root.
    Normalizes paths to handle '..' and remove leading '/'.
    """
    if not src:
        return None
    
    if not doc_href:
        # Assume src is relative to the EPUB root (e.g., OEBPS/)
        resolved = PurePosixPath(src)
    else:
        base = PurePosixPath(doc_href).parent
        resolved = base / src
    
    # Normalize the path (handles '..' and other relative components), ensuring posix separators
    resolved_str = os.path.normpath(str(resolved)).replace(os.sep, '/')
    # Remove leading '/' if present, as EPUB hrefs are stored without it
    resolved_str = resolved_str.lstrip("/")
    # EPUB hrefs are often stored without leading '..', so strip it if present
    if resolved_str.startswith("../"):
        resolved_str = resolved_str[3:]
    
    return resolved_str


def translate_epub(
    file_path: str,
    app_pipeline: BasePipeline,
    checkpoint_every_pages=0,
    socketio: SocketIO = None,
):
    with logger.begin_event(
        "Translate EPUB file", checkpoint_every_pages=checkpoint_every_pages, file_path=file_path
    ) as ctx:
        if app_pipeline.image_cleaning_app.get_sel_app_name() == "none":
            app_pipeline.switch_cleaning_app("blur")
        if "amg" in app_pipeline.image_redrawing_app.get_sel_app_name():
            app_pipeline.switch_redrawing_app("insane")

        ctx.log(f"Using image cleaning/redrawing modes", cleaning_mode=app_pipeline.image_cleaning_app.get_sel_app_name(), redrawing_mode=app_pipeline.image_redrawing_app.get_sel_app_name())

        e_book = epub.read_epub(file_path)

        write_book_id = str(uuid.uuid4())
        book_folder_path = f"{save_folder_path}/{write_book_id}"
        book_checkpoint_folder_path = f"{save_folder_path}/{write_book_id}/checkpoints"
        make_folder(book_folder_path)
        make_folder(book_checkpoint_folder_path)

        context_state = ContextState()

        # Progress is based on # of sentences - not pages.
        # pages_len = len(list(e_book.get_items()))
        sentences_len = 0

        i = 0  # Every page, save a checkpoint.
        j = 2  # Every few translations (and 1 initially), ping the progress.

        min_per_doc = 3

        # Once an image is processed, do not process it again.
        # For some reason this library reiterates over image elements multiple times.
        processed_image_hrefs = set([])

        # First get sentences_len for progress updates.
        for doc in e_book.get_items():
            try:
                content = doc.content.decode("utf-8")

                soup = BeautifulSoup(content, features="html.parser")
                replacement_count = 0

                # Find text in <p> elements. If too little was found, try in <div> elements instead.
                p_results = soup.find_all("p")
                for p in p_results:
                    p_text = p.get_text()  # Strip HTML
                    p_text = p_text.strip()

                    if len(p_text) > 0:
                        replacement_count += 1

                if replacement_count < min_per_doc:
                    replacement_count = 0

                    # If little to no text was extracted, we will assume that the EPUB stores the text in <div> elements instead of <p>.
                    div_results = soup.find_all("div")

                    for d in div_results:
                        d_text = d.get_text()  # Strip HTML
                        d_text = d_text.strip()

                        if len(d_text) > 0:
                            replacement_count += 1

                sentences_len += replacement_count
            except UnicodeError:
                pass

        # Now we actually translate the pages.
        for idx, doc in enumerate(e_book.get_items()):
            ctx.log("Checking page", page_idx=idx)

            replacement_count = 0
            images_replacement_count = 0

            # doc.content returns a bytes object. If we simply stringify it, we get... an ugly mess.
            # Instead, we want to utf-8 decode it. This gives us a nice mostly-probably-okay string representation.
            try:
                content = doc.content.decode("utf-8")

                soup = BeautifulSoup(content, features="html.parser")

                # Process any <img> tags in this HTML page
                ### (AI-assisted)
                for img_tag in soup.find_all(["img", "image"]):
                    ctx.log("Found embedded <img> tag to translate", img_tag=str(img_tag)[:200])

                    src = img_tag.get("src") or img_tag.get("xlink:href") or img_tag.get("href")
                    # What the hell is an xlink? Even AI doesn't know! TODO (determine what other hrefs we're missing if any).

                    href = _resolve_epub_href(getattr(doc, "href", None) or getattr(doc, "xlink:href", None), src)
                    ctx.log("Resolved image href", src=src, resolved_href=href)
                    if not href:
                        continue

                    if href in processed_image_hrefs:
                        ctx.log("Image already processed, skipping", href=href)
                        continue

                    image_item = e_book.get_item_with_href(href)
                    ctx.log("Retrieved image item", image_item_exists=image_item is not None, media_type=getattr(image_item, "media_type", "unknown"), format=getattr(image_item, "format", "unknown"))
                    if not image_item or not getattr(image_item, "media_type", "").startswith("image/"):
                        continue

                    try:
                        img = Image.open(BytesIO(image_item.content)).convert("RGB")
                        translated_img = translate_img(app_pipeline, img)
                        buf = BytesIO()
                        translated_img.save(buf, format="PNG")
                        image_item.content = buf.getvalue()
                        processed_image_hrefs.add(href)

                        images_replacement_count += 1
                    except Exception as e:
                        ctx.log("Error processing embedded image", page_idx=idx, src=src)
                        logger.event_exception(ctx)
                ###

                # Find text in <p> elements. If too little was found, try in <div> elements instead.

                p_results = soup.find_all("p")
                ctx.log("<p> elements counted", p_results_len=len(p_results))

                for p in p_results:
                    p_text = p.get_text()  # Strip HTML
                    p_text = p_text.strip()

                    if len(p_text) > 0:
                        # We assume all the text in an HTML paragraph element constitutes a sentence.
                        try:
                            if len(p_text) > 2500:
                                raise RuntimeError("Paragraph text is very long, skipping translation (likely non-text)")

                            new_text = translate_one_sentence(
                                p_text, app_pipeline, context_state
                            )
                            p.string = new_text
                            replacement_count += 1
                        except Exception as e:
                            # Typically out of context.
                            ctx.log("Error translating paragraph text", page_idx=idx, p_text=p_text)
                            logger.event_exception(ctx)

                        j += 1

                        if j % 3 == 0:
                            # Need calls every now and then so the websocket doesn't lose "interest".

                            emit_progress(socketio, j, sentences_len)
                            socketio.sleep()

                if replacement_count < min_per_doc:
                    # If little to no text was extracted, we will assume that the EPUB stores the text in <div> elements instead of <p>.
                    div_results = soup.find_all("div")

                    ctx.log("<div> elements counted", p_results_len=len(div_results))

                    for d in div_results:
                        d_text = d.get_text()  # Strip HTML
                        d_text = d_text.strip()

                        if len(d_text) > 0:
                            try:
                                if len(d_text) > 2500:
                                    raise RuntimeError("Div text is very long, skipping translation (likely non-text)")

                                new_text = translate_one_sentence(
                                    d_text, app_pipeline, context_state
                                )
                                d.string = new_text
                                replacement_count += 1
                            except Exception as e:
                                # Typically out of context.
                                ctx.log("Error translating div text", page_idx=idx, d_text=d_text)
                                logger.event_exception(ctx)

                            j += 1

                            if j % 3 == 0:
                                # Need calls every now and then so the websocket doesn't lose "interest".

                                emit_progress(socketio, j, sentences_len)
                                socketio.sleep()

                if replacement_count > 0:
                    ctx.log("Translated page text", page_idx=idx, sentences_translated=replacement_count)

                    # If some text was translated, then use the modified page as the new page.
                    # Content must be re-encoded to utf-8.
                    doc.content = str(soup).encode("utf-8")
                elif images_replacement_count == 0:
                    raise RuntimeError("No text/images found in page (not HTML?) - skipping to image check.")
            except (UnicodeDecodeError, RuntimeError):
                # Some pages have no text. They can be ignored and left as is.
                ctx.log("UnicodeError while parsing page text.", page_idx=idx)

                """
                This causes images to be iterated over more than once (after all text pages are done).
                TODO: Investigate using this logic alone instead of iterating over images with the HTML logic.

                # Perhaps the page only contains images in a certain format - translate the image instead.
                # (Note: This image logic was AI assisted - Ebooklib is tricky to work with)
                # (Also note: This is a very rare case - most image pages are just HTML (See above))
                if hasattr(doc, 'media_type') and doc.media_type.startswith('image/'):
                    with logger.begin_event("Found image! Processing...", page_idx=idx, media_type=doc.media_type) as subctx:
                        try:
                            # Load the image as PIL Image
                            img = Image.open(BytesIO(doc.content)).convert("RGB")
                            subctx.log("Image loaded", image_size=img.size)

                            translated_img = translate_img(app_pipeline, img)

                            # Save the processed image back to bytes, preserving format
                            buf = BytesIO()
                            translated_img.save(buf, format=img.format)
                            doc.content = buf.getvalue()

                            subctx.log("Image processed and replaced", page_idx=idx)
                        except Exception as e:
                            subctx.log("Error processing image", page_idx=idx, error=str(e))
                else:
                    # Skip other binary items (e.g., CSS, fonts)
                    ctx.log("Skipping non-text, non-image item", page_idx=idx, media_type=getattr(doc, 'media_type', 'unknown'))

                    try:
                        ctx.log("Page HTML", content=soup.prettify()[:500])
                    except Exception as e:
                        ctx.log("Error logging page HTML", error=str(e))
                """

            i += 1

            if checkpoint_every_pages != 0 and i % checkpoint_every_pages == 0:
                write_path = f"{book_checkpoint_folder_path}/checkpoint_{i}.epub"
                ctx.log(f"Saving book checkpoint", write_path=write_path)
                epub.write_epub(write_path, e_book)

            emit_progress(socketio, j, sentences_len)
            socketio.sleep()

        final_path = f"{book_folder_path}/new_book.epub"
        epub.write_epub(final_path, e_book)
        ctx.log(f"Saving final book", write_path=final_path)
