import isDev from "electron-is-dev";
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

  // Prevent electron-builder from rechanging title to "Mango"
  ocrWindow.on('page-title-updated', (e) => {
    e.preventDefault();
  });

  const htmlPath = isDev ? "index.html" : path.join(__dirname, "./index.html");
  console.log(`Loading OCR box HTML from path: ${htmlPath}`);

  ocrWindow.loadFile(htmlPath, {
    query: { mode: "ocrbox", boxid: `${opts.boxId}` },
  }); // NOTE: Using query parameters may result in caching. Not sure if this is bad... yet.

  if (isDev) ocrWindow.webContents.openDevTools({ mode: "undocked" });

  return ocrWindow;
};
