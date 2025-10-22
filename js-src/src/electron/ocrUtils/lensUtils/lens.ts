import SharedGlobalShortcuts from "../sharedGlobalShortcuts";
import { scanScreenGiveData } from "../../../flaskcomms/lensBackendComms";
import isDev from "../../../electronDevMode";
import { BrowserWindow } from "electron";
import path from "path";
import { ElectronState } from "../../../types/ElectronState";

const openWindow = (
  x: number,
  y: number,
  width: number,
  height: number,
  text: string
) => {
  console.log(
    `Making window with X,Y=[${x}, ${y}] and size=[${width}, ${height}] and text="${text}"`
  );

  const lensWindow = new BrowserWindow({
    width: width + 50, // Most detections are often too tight.
    height,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      devTools: isDev,
      backgroundThrottling: false,
    },
    frame: false,
    resizable: true,
    x,
    y,
    transparent: true,
    alwaysOnTop: true,
    icon: path.join(__dirname, "Icon.png"),
    title: "Lens Window",
  });

  lensWindow.setSkipTaskbar(true);

  lensWindow.setAlwaysOnTop(true, "screen-saver", 1);
  lensWindow.setVisibleOnAllWorkspaces(true);
  lensWindow.setFullScreenable(false);

  // Prevent electron-builder from rechanging title to "Mango"
  lensWindow.on("page-title-updated", (e) => {
    e.preventDefault();
  });

  const htmlPath = isDev ? "index.html" : path.join(__dirname, "./index.html");
  console.log(`Loading lens box HTML from path: ${htmlPath}`);

  lensWindow.loadFile(htmlPath, {
    query: { mode: "lens", text },
  });

  if (isDev) lensWindow.webContents.openDevTools({ mode: "undocked" });

  return lensWindow;
};

const handleLens = async () => {
  const response = await scanScreenGiveData();

  const windows: BrowserWindow[] = [];
  for (const item of response.items) {
    const wind = openWindow(item.x, item.y, item.width, item.height, item.text);
    windows.push(wind);
  }

  return windows;
};

export const registerLens = (
  activationKey: any,
  globalState: ElectronState
) => {
  console.log("Registering lens data...");

  const lensState = {
    windows: [] as BrowserWindow[],
    cb: null as null | string,
    inProgress: false,
  };

  const destroyWindows = () => {
    console.log("Destroying lens windows...");

    for (const wind of lensState.windows) {
      try {
        wind.destroy();
      } catch {
        continue;
      }
    }

    lensState.windows = [];
  };

  const onActivation = async () => {
    console.log("Lens key pressed...");

    if (lensState.windows.length > 0) {
      // Destroy all windows rather than translating screen on first press.
      destroyWindows();
      return;
    }

    if (lensState.inProgress) return;
    lensState.inProgress = true;

    console.log("Scanning screen...");

    for (const manager of globalState.managers) {
      manager.cloakBox();
    }

    const windows = await handleLens();

    for (const manager of globalState.managers) {
      manager.revealBox();
    }

    lensState.windows = windows;
    lensState.inProgress = false;
  };

  if (activationKey !== "Escape") {
    lensState.cb = SharedGlobalShortcuts.register(activationKey, onActivation);
  }

  // Cleanup function.
  return () => {
    console.log("Cleaning up lens data...");

    if (lensState.cb !== null)
      SharedGlobalShortcuts.unregister(activationKey, lensState.cb);

    destroyWindows();
  };
};
