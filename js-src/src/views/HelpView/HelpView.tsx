import React from "react";
import BaseView from "../BaseView";
import BaseHelp from "./components/BaseHelp";
import { CssBaseline, Stack, ThemeProvider } from "@mui/material";
import { appTheme } from "../../appTheme";

const questions = [
  {
    title: "How do I use this to translate games with Textractor?",
    steps: [
      'Navigate to the "Text" tab.',
      "Click the shiny purple button on the bottom left.",
      `
      A detached box will appear on the screen.
      This box will automagically translate any text in the clipboard and show the translation.
      `,
      `Then, load Textractor and enable the "Copy to clipboard" extension in it. Now when Textractor hooks into a game, it will read and copy untranslated text into the clipboard, and Mango will translate it.`,
    ],
  },
  {
    title: "How do I use this to translate games without Textractor?",
    steps: [
      'Navigate to the "Text" tab, and click the blue button on the bottom left.',
      `You will be prompted to select a use case. Select the use case titled "1 box" with the description "I want a box that reads text on the screen when I press a button."`,
      `Navigate back to the "Text" tab, and click the shiny purple button.`,
      `A detached box will pop up on the screen. Drag this box wherever the game text will be. The box can be resized and moved by dragging on the edges.`,
      `Press "1" to translate whatever is behind this detached box.`,
    ],
  },
  {
    title: "How do I use this to translate images?",
    steps: [
      `Navigate to the "Image" tab, and then drag and drop your image files into the box.`,
      `A new folder will be created, and the translated images will be sent there. You can see these folders by clicking on the "Library" text on the right.`,
      `
      By default, image files will be translated and saved as AMG files, which can currently only be seen with Mango (don't have a good inpainting solution yet).
      The output will be saved under Windows Documents - look for a folder called "Mango".
      `,
      `Want to save the images as normal files anyways? Select any of the other redrawing methods on the bottom right. You may also want to change the cleaning method.`,
    ],
  },
  {
    title: "(Buggy) How do I use this to translate EPUB files?",
    steps: [
      `Navigate to the "Book" tab, and then drag and drop ONE EPUB file into the box.`,
      `The process will take some time, but every now and then a partially translated EPUB will be created for the reader. The output will be saved under Windows Documents - look for a folder called "Mango" in the documents folder.`,
    ],
  },
  {
    title: "How do I translate from a different language?",
    steps: [
      `Navigate to the "Settings" tab, and then change the translation model and text recognition model. Or just change the Preset to one that uses your desired language.`,
    ],
  },
  {
    title: "How can I improve the translation quality?",
    steps: [
      `Take a look at the "Settings" tab! There are a lot of things you can configure, such as...`,
      'A. Using a spelling correction model (e.g: "ProFill").',
      'B. Translating images? Try using a line detection model (like "D-FINE Line EXO-Massive") in addition to a text detection model!',
      "C. Increasing / decreasing max context might help increase the quality.",
      "D. Tinkering with the decoding parameters can improve quality too. Try setting the beam size to 5 or 10 (or even 15 if you're daring...)",
      "E. Enabling a reranker model and using MBR decoding can sometimes improve quality too.",
      "F. If using the detached text window to translate games, you may want to use Textractor (to avoid any potential OCR errors).",
      'G. Use a bigger translation model, such as "Japanese-2-English Gem".',
    ],
  },
  {
    title: "How can I speed up the process?",
    steps: [
      `Take a look at the "Settings" tab! There are a lot of things you can configure, such as...`,
      "A. Decreasing max context will slightly improve speed.",
      "B. Reducing beam size will improve speed. (e.g: setting beam size to 1)",
      "C. (The big one!) Enable CUDA. In CUDA mode, processing can be MUCH faster (sometimes even up to 10x!), but it requires a CUDA compatible GPU.",
      "D. Using smaller models (such as using no text line detection model, or a smaller OCR model).",
    ],
  },
  {
    title: "How do I use this to translate web pages?",
    steps: [
      'Navigate to the "Web" tab.',
      "Paste the weblink on the top input field.",
      "You probably only want to translate text within certain HTML elements. You can use CSS selectors to only translate certain elements (see the syntax from BeautifulSoup docs).",
      `When you're done, simply select a text field and press "Enter".`,
      'By default, "Preview Selected Elements" is on. This way, the UNTRANSLATED text will be retrieved so that you can ensure only the expected text is retrieved with CSS selectors.',
      'Alternatively, you can manually copy all the desired text on a web page and just paste it all in the bottom box in the "Text" tab.',
    ],
  },
  {
    title: "How do I manually typeset images in this app?",
    steps: [
      'First, translate an image with the redrawing mode set to "Annotate".',
      'While viewing the image in this app, click the button saying "Edit" below it.',
      "Now you can click on a text to change the content or style it with the toolbar on the left.",
      "Custom fonts can be added by placing font files in the resources/fonts folder (relative to the EXE location for Mango).",
      "If you like the way one of your text boxes looks like, you can give the preset a name and save it, allowing it to be reused quickly.",
      "Once done, save the image with the button on the bottom left and wait a few seconds. A PNG file will be saved in the same folder as the annotated image file.",
    ],
  },
  {
    title:
      "How do I add new fonts or replace the font used in the detached box?",
    steps: [
      "New font files can be added in the Mango application folder, under the resources/fonts folder.",
      "Simply drop OTF/TTF files here to add them as available fonts for use in image editing.",
      'To replace the detached box font, just name the desired font "ocrbox.ttf".',
    ],
  },
  /* {
    title: "The translator is hanging. Can I force stop it?",
    steps: [
      "Yes - translation jobs can be forcefully stopped. Press CRTL + SHIFT + Q",
    ],
  }, */
];

const HelpView = () => {
  return (
    <ThemeProvider theme={appTheme}>
      <CssBaseline>
        <BaseView noPadding>
          <Stack spacing={4} sx={{ width: "90%" }}>
            {questions.map((q) => (
              <BaseHelp title={q.title} steps={q.steps} key={q.title} />
            ))}
          </Stack>
        </BaseView>
      </CssBaseline>
    </ThemeProvider>
  );
};

export default HelpView;
