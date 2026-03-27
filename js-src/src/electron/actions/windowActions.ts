import { app, clipboard, BrowserWindow } from "electron";
import ElectronCommands from "../../types/ElectronCommands";
import { GatewayAction } from "../../types/GatewayAction";
import { createHelpWindow } from "../createHelpWindow";

const closeWindow: GatewayAction = {
  command: ElectronCommands.CLOSE_APP,
  commandType: "handle",
  fn: (_e, _w, state, store) => {
    console.log("Closing app normally...");

    try {
      for (const manager of state.managers) {
        if (manager.ocrWindow !== null) {
          manager.tearDownBox(true, store);
        }
      }
    } catch (exc) {
      console.log(exc);
    }

    BrowserWindow.getAllWindows().forEach((win) => {
      if (!win.isDestroyed()) {
        try {
          win.destroy();
        } catch (err) {
          console.error(err);
        }
      }
    });

    try {
      app.quit();
    } catch (error) {
      console.error(error);
    }
  },
};

const expandWindow: GatewayAction = {
  command: ElectronCommands.EXPAND_APP,
  commandType: "handle",
  fn: (e, mainWindow) => {
    if (mainWindow.isMaximized()) {
      mainWindow.unmaximize();
    } else {
      mainWindow.maximize();
    }
  },
};

const hideApp: GatewayAction = {
  command: ElectronCommands.HIDE_APP,
  commandType: "handle",
  fn: (e, mainWindow) => {
    mainWindow.minimize();
  },
};

// Help window is NOT the main window.
const openHelpWindow: GatewayAction = {
  command: ElectronCommands.OPEN_HELP_WINDOW,
  commandType: "handle",
  fn: () => {
    createHelpWindow();
  },
};

const readClipboard: GatewayAction = {
  command: ElectronCommands.READ_CLIPBOARD,
  commandType: "handle",
  fn: async () => {
    return clipboard.readText();
  },
};

const flashFrame: GatewayAction = {
  command: ElectronCommands.FLASH_FRAME,
  commandType: "handle",
  fn: (e, mainWindow) => {
    const win = mainWindow as BrowserWindow; // TODO: Why is my interface using BasicBrowserWindow again? I forgor.
    if (win.isFocused()) return;

    win.flashFrame(true);

    win.once("focus", () => {
      win.flashFrame(false);
    });
  },
};

export default [
  closeWindow,
  expandWindow,
  hideApp,
  openHelpWindow,
  readClipboard,
  flashFrame,
];
