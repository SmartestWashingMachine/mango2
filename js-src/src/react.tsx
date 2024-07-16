import * as React from "react";
import * as ReactDOM from "react-dom";
import { createRoot } from "react-dom/client";
import "@fontsource/roboto/300.css";
import "@fontsource/roboto/400.css";
import "@fontsource/roboto/500.css";
import "@fontsource/roboto/700.css";
import App from "./App";
import BoxApp from "./views/OcrBoxView/BoxApp";
import { MainGateway } from "./utils/mainGateway";
import HelpView from "./views/HelpView/HelpView";

const container = document.getElementById("react-app");
const root = createRoot(container!);

const queryParams = new URLSearchParams(window.location.search);
const modeParam = queryParams.get("mode");
const boxIdParam = queryParams.get("boxid") as string;

if (modeParam === "ocrbox") {
  root.render(<BoxApp boxId={boxIdParam} />);
} else if (modeParam === "help") {
  root.render(<HelpView />);
} else {
  root.render(<App />);
}

// Load fonts.
const loadFonts = async () => {
  // This will fail for HelpView but whatever.
  const { fontPaths, fontNames } = await MainGateway.retrieveFontFiles();

  for (let i = 0; i < fontPaths.length; i++) {
    const fontP: string = fontPaths[i];
    const fontN = fontNames[i];

    const fontFace = new FontFace(fontN, `url("${fontP}")`);
    document.fonts.add(fontFace);

    await fontFace.load();
  }

  // "Why do we add this too? It seems inefficient!" Dom-to-image (the package used to save images) doesn't copy font faces loaded above. This section ensures that the fonts are copied when saving the image.
  // "Why create fonts like above then?" Because we can easily access the fonts in other components without hacking up a global structure manually.
  let markup = (fontPaths as string[])
    .map((p, idx) =>
      [
        "@font-face {\n",
        "\tfont-family: '",
        fontNames[idx],
        "';\n",
        "\tfont-style: 'normal';\n",
        "\tfont-weight: 'normal';\n",
        `\tsrc: url("${p}")\n`,
        "}\n",
      ].join("")
    )
    .join("");

  let styles = document.createElement("style");
  document.head.appendChild(styles);

  styles.setAttribute("type", "text/css");
  styles.innerHTML = markup;
};

loadFonts();
