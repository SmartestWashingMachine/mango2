import { app, BrowserWindow } from "electron";
import path from "path";
import { ElectronState } from "./types/ElectronState";
import { initializeModelNames } from "./flaskcomms/setFlaskSettings";
import { closePython, loadPython } from "./electron/loadPython";
import isDev from "electron-is-dev";
import { initializeStore } from "./electron/persistentStore";
import { makeLogs } from "./electron/electronLogging";
import ElectronChannels from "./types/ElectronChannels";
import { createGatewayActions } from "./electron/createGatewayActions";
import configStoreActions from "./electron/actions/configStoreActions";
import fileActions from "./electron/actions/fileActions";
import ocrBoxActions from "./electron/actions/ocrBoxActions";
import textHistoryActions from "./electron/actions/textHistoryActions";
import windowActions from "./electron/actions/windowActions";
import { OcrBoxManager } from "./electron/ocrUtils/ocrBox";
import { createEssentialFolders } from "./electron/fileUtils/createEssentialFolders";
import { OPTIONS_PRESETS } from "./utils/boxPresets";

import http from 'http';
import { Server } from 'socket.io';

app.commandLine.appendSwitch('disable-renderer-backgrounding');
app.commandLine.appendSwitch('disable-background-timer-throttling');

app.disableHardwareAcceleration();

makeLogs();

const store = initializeStore();

// Not to be confused with the store. This state is used to display stuff on the client only and is NOT persistent.
const electronState: ElectronState = {
  managers: [],
  texts: [],
};

const createWindow = () => {
  const win = new BrowserWindow({
    width: 800,
    height: 680,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"), // Preload.js must have an absolute path.
      devTools: isDev,
    },
    icon: path.join(__dirname, "Icon.png"),
    opacity: 0, // Is set to 1 later on.
    frame: isDev, // No menu bars nor top bar.
    resizable: true,
    titleBarStyle: isDev ? "default" : "hidden",
    backgroundColor: '#FFF',
  });

  console.log("Window created.");

  return win;
};

const openShellArg = app.commandLine.hasSwitch("showpy");

const subprocess = isDev ? null : loadPython(openShellArg);

app.whenReady().then(async () => {
  await createEssentialFolders();

  let mainWindow = createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) mainWindow = createWindow();
  });

  // Emit store data changes to client.
  store.onDidAnyChange((s, oldState) => {
    mainWindow.webContents.send(ElectronChannels.EMIT_STORE_DATA, s, oldState);
  });

  // Initialize OCR box managers.
  const boxes = store.get("boxes") as any[];

  if (boxes.length === 0) {
    const boxes = [{ ...OPTIONS_PRESETS[0].options, boxId: 'firstbox' }];
    store.set("boxes", boxes);
  }

  electronState.managers = boxes.map(
    (b) => new OcrBoxManager(b.boxId, store, electronState.texts)
  );

  // Define all commands and other listeners for client -> <- electron communications.
  const ALL_ACTIONS = [
    ...configStoreActions,
    ...fileActions,
    ...ocrBoxActions,
    ...textHistoryActions,
    ...windowActions,
  ];
  createGatewayActions(electronState, mainWindow, store, ALL_ACTIONS);

  const server = http.createServer();

  // TODO: Do I need expressJS? I hope not.

  const io = new Server(server, { pingTimeout: 100000, maxHttpBufferSize: 1e10 });
  io.on('connection', (socket) => {
    // Act as a bridge. Cybersecurity says what?
    socket.onAny((evName, ...args) => {
      // console.log(`Emitting ${evName}`);

      const browWindows: BrowserWindow[] = [mainWindow, ...electronState.managers.map(x => x.ocrWindow)];
      for (const win of browWindows) {
        if (win) {
          win.webContents.send(`bridge_${evName}`, ...args);
        }
      }
    });
  });

  server.listen(5100, () => {
    console.log('Experimental WS server listening on port 5100.');
  });

  // API call.
  await initializeModelNames(store.store);

  mainWindow.setOpacity(1);
  mainWindow.loadFile(path.join(__dirname, "./index.html"));
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    if (!isDev) closePython(subprocess);
    app.quit();
  }
});
