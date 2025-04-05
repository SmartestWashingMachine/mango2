import isDev from "../../electronDevMode";
import path from "path";
import { BrowserWindow, globalShortcut, clipboard, screen } from "electron";

export type CreateOcrWindowOpts = {
  width: number;
  height: number;
  xOffset: number;
  yOffset: number;
  boxId: string;
};

export const createOcrWindow = (opts: CreateOcrWindowOpts) => {
  const ocrWindow = new BrowserWindow({
    width: opts.width,
    height: opts.height,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"), // Preload.js must have an absolute path.
      devTools: isDev, // for debugging
      // backgroundThrottling is critical: If True, then text boxes that are placed behind other text boxes will not be rerendered until the window is moved to the foreground.
      // This is annoying, since it means that text boxes behind other text boxes will not be hidden automatically.
      backgroundThrottling: false,
    },
    frame: false,
    resizable: true,
    x: opts.xOffset,
    y: opts.yOffset,
    transparent: true,
    alwaysOnTop: true,
    icon: path.join(__dirname, "Icon.png"),
    title: "Text Window",
  });

  ocrWindow.setSkipTaskbar(true);

  ocrWindow.setAlwaysOnTop(true, "screen-saver", 1);
  ocrWindow.setVisibleOnAllWorkspaces(true);
  ocrWindow.setFullScreenable(false);

  // Prevent electron-builder from rechanging title to "Mango"
  ocrWindow.on("page-title-updated", (e) => {
    e.preventDefault();
  });

  /*
  ocrWindow.on("blur", () => {
    ocrWindow.setAlwaysOnTop(true, "screen-saver", 1);
    ocrWindow.show(); // ?
  });*/

  const htmlPath = isDev ? "index.html" : path.join(__dirname, "./index.html");
  console.log(`Loading OCR box HTML from path: ${htmlPath}`);

  ocrWindow.loadFile(htmlPath, {
    query: { mode: "ocrbox", boxid: `${opts.boxId}` },
  }); // NOTE: Using query parameters may result in caching. Not sure if this is bad... yet.

  if (isDev) ocrWindow.webContents.openDevTools({ mode: "undocked" });

  return ocrWindow;
};
