import { app } from "electron";
import ElectronCommands from "../../types/ElectronCommands";
import { GatewayAction } from "../../types/GatewayAction";
import { createHelpWindow } from "../createHelpWindow";

const closeWindow: GatewayAction = {
  command: ElectronCommands.CLOSE_APP,
  commandType: "handle",
  fn: (_e, _w, state, store) => {
    try {
      for (const manager of state.managers) {
        if (manager.ocrWindow !== null) {
          manager.tearDownBox(true, store);
        }
      }
    } catch (exc) {
      console.log(exc);
    }

    app.quit();
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

export default [closeWindow, expandWindow, hideApp, openHelpWindow];
