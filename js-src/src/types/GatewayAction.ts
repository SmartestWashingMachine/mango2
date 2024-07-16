import ElectronChannels from "./ElectronChannels";
import ElectronCommands from "./ElectronCommands";
import { ElectronState } from "./ElectronState";
import { StoreAdapter } from "./ElectronStore";

export type BasicBrowserWindow = {
  webContents: {
    send: (responseCommand: ElectronCommands, payload: any) => void;
  };
  unmaximize: () => void;
  maximize: () => void;
  isMaximized: () => boolean;
  minimize: () => void;
};

export type BasicIpcEvent = {
  sender: {
    send: (responseChannel: ElectronChannels, ...payload: any[]) => void;
  };
};

export type GatewayAction = {
  command: ElectronCommands;
  commandType: "handle" | "on";
  fn: (
    e: BasicIpcEvent,
    window: BasicBrowserWindow,
    state: ElectronState,
    store: StoreAdapter,
    ...args: any[]
  ) => any | Promise<any>;
};
