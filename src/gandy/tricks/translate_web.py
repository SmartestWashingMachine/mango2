from bs4 import BeautifulSoup
from bs4.element import Comment
import requests
from gandy.state.context_state import context_state
from gandy.utils.text_processing import add_seps
from gandy.utils.fancy_logger import logger
from gandy.state.config_state import config_state
from gandy.app import socketio

# The previous few requests are cached in case the user wants to make quick edits to the CSS selector field.
class WebCache:
    def __init__(self) -> None:
        self.web_links = []  # list of strings.
        self.web_contents = []  # each index here matches the web_link.

        self.max_cached = 10

    def to_soup(self, web_content):
        return BeautifulSoup(web_content, "html.parser")

    def add_to_cache(self, link: str, cont):
        self.web_links.append(link)
        self.web_contents.append(cont)

        if len(self.web_links) > self.max_cached:
            self.web_links = self.web_links[1:]
            self.web_contents = self.web_contents[1:]

    def retrieve_contents(self, web_link: str):
        with logger.begin_event("Retrieve HTML content from URL", url=web_link) as ctx:
            try:
                idx = self.web_links.index(web_link)
                found_contents = self.web_contents[idx]

                ctx.log("Found URL in cache.")

                return self.to_soup(found_contents)
            except:
                # Not in cache. Update.
                ctx.log("URL not in cache. Creating.")

                page = requests.get(
                    web_link, headers={"User-Agent": "Mozilla/5.0"}
                )  # User agent is needed for some sites.
                new_contents = page.content.decode("utf-8", "ignore")
                self.add_to_cache(web_link, new_contents)
                return self.to_soup(new_contents)


web_cache = WebCache()


def tag_visible(element):
    if element.parent.name in [
        "style",
        "script",
        "head",
        "title",
        "meta",
        "[document]",
    ]:
        return False
    if isinstance(element, Comment):
        return False
    return True


def get_texts_in_soup(item):
    texts = item.find_all(text=True)
    visible_texts = list(filter(tag_visible, texts))
    visible_texts = [str(s).strip() for s in visible_texts]
    visible_texts = [s for s in visible_texts if len(s) > 0]

    return visible_texts


def retrieve_texts(link, content_filter=None):
    soup = web_cache.retrieve_contents(link)

    output = []

    # From: https://stackoverflow.com/questions/1936466/beautifulsoup-grab-visible-webpage-text
    if content_filter is not None:
        selected_items = soup.select(content_filter)

        for item in selected_items:
            output.extend(get_texts_in_soup(item))
    else:
        output.extend(get_texts_in_soup(soup))

    return output

def map_texts(texts):
    return "\n\n".join(texts).strip()

def translate_web(link, app_pipeline, content_filter=None, do_preview=False):
    """
    Given a link to a webpage, retrieve all text inside it and translate it with the app pipeline. Returns a list of strings.

    This may be unsafe / unreliable, depending on the webpage.
    """
    texts = retrieve_texts(
        link, content_filter
    )  # Get untranslated texts as list of strings.

    translated_texts = []

    for t in texts:
        if len(t) == 0 or t is None:
            continue

        if not do_preview:
            text = add_seps(context_state.prev_source_text_list + [t])

            (new_text, processed_src) = app_pipeline.text_to_text(
                text,
                use_stream=None,
                return_source_text=True,
            )

            context_state.update_source_list(
                processed_src[0], config_state.n_context,
            )

            context_state.update_target_list(
                new_text[0],
                config_state.n_context,
            )

            translated_texts.extend(new_text)  # Should only be one element.
        else:
            translated_texts.append(t)

        socketio.patched_emit('item_taskweb', { 'text': map_texts(translated_texts) })

    socketio.patched_emit('done_taskweb', { 'text': map_texts(translated_texts) })
    return map_texts(translated_texts)
