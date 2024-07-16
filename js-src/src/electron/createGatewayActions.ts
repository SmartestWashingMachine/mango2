import { GatewayAction } from "../types/GatewayAction";
import { ElectronState } from "../types/ElectronState";
import { BrowserWindow, ipcMain } from "electron";
import { StoreAdapter } from "../types/ElectronStore";

export const createGatewayActions = (
  state: ElectronState,
  win: BrowserWindow,
  store: StoreAdapter,
  actions: GatewayAction[]
) => {
  for (const act of actions) {
    if (act.commandType === "handle") {
      ipcMain.handle(act.command, (e, ...args) =>
        act.fn(e, win, state, store, ...args)
      );
    } else if (act.commandType === "on") {
      ipcMain.on(act.command, (e, ...args) =>
        act.fn(e, win, state, store, ...args)
      );
    }
  }
};
