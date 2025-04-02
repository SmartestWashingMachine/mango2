import isDev from "../electronDevMode";
import path from "path";
import { BrowserWindow, screen } from "electron";

export const createHelpWindow = () => {
  const primaryDisplay = screen.getPrimaryDisplay();
  const { width, height } = primaryDisplay.workAreaSize;

  const win = new BrowserWindow({
    width: Math.floor(width * 0.4),
    height: Math.floor(height * 0.75),
    webPreferences: {
      devTools: false,
    },
    frame: true,
    resizable: true,
    x: 0,
    y: 0,
    transparent: false,
    alwaysOnTop: true,
    icon: path.join(__dirname, "Icon.png"),
    title: "Mango Help",
  });

  win.center();

  const htmlPath = isDev ? "index.html" : path.join(__dirname, "./index.html");
  console.log(`Loading help window HTML from path: ${htmlPath}`);

  win.loadFile(htmlPath, {
    query: { mode: "help" },
  });

  if (isDev) win.webContents.openDevTools({ mode: "undocked" });

  return win;
};
