import { app, BrowserWindow, screen, Menu, session } from "electron";
import path from "path";
import { ElectronState } from "./types/ElectronState";
import { initializeModelNames } from "./flaskcomms/setFlaskSettings";
import { closePython, loadPython } from "./electron/loadPython";
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
import { getDefaultBoxes } from "./utils/boxPresets";

import http from "http";
import { Server } from "socket.io";
import isDev from "./electronDevMode";
import { readDangerousConfigMain } from "./dangerousConfig/readDangerousConfigMain";
import dangerousConfigActions from "./electron/actions/dangerousConfigActions";

if (!isDev) Menu.setApplicationMenu(null);

app.commandLine.appendSwitch("disable-renderer-backgrounding");
app.commandLine.appendSwitch("disable-background-timer-throttling");

// Bricks OCR window screenshotting. The fudge ElectronJS? Why do you have to be shady?
// app.disableHardwareAcceleration();

makeLogs();

const store = initializeStore();

// Not to be confused with the store. This state is used to display stuff on the client only and is NOT persistent.
const electronState: ElectronState = {
  managers: [],
  texts: [],
};

const lockTop = app.commandLine.hasSwitch("locktop"); // For dev usage.

// Code not mine. From: https://github.com/electron/electron/issues/526
const restoreWindowBounds = (win: BrowserWindow) => {
  const savedBounds = store.get("mainBounds") as any;

  if (savedBounds !== undefined && savedBounds !== null) {
    const screenArea = screen.getDisplayMatching(savedBounds).workArea;
    if (
      savedBounds.x > screenArea.x + screenArea.width ||
      savedBounds.x < screenArea.x ||
      savedBounds.y < screenArea.y ||
      savedBounds.y > screenArea.y + screenArea.height
    ) {
      win.setBounds({ x: 0, y: 0, width: 800, height: 680 });
    } else {
      win.setBounds(store.get("mainBounds"));
    }
  }

  win.on("close", () => {
    store.set("mainBounds", win.getBounds());
  });
};

const openShellArg = app.commandLine.hasSwitch("showpy");

const createWindow = () => {
  const win = new BrowserWindow({
    webPreferences: {
      preload: path.join(__dirname, "preload.js"), // Preload.js must have an absolute path.
      devTools: isDev,
    },
    icon: path.join(__dirname, "Icon.png"),
    opacity: 0, // Is set to 1 later on.
    frame: isDev, // No menu bars nor top bar.
    resizable: true,
    titleBarStyle: isDev ? "default" : "hidden",
    backgroundColor: "#FFF",
    alwaysOnTop: lockTop || undefined,
    skipTaskbar: !openShellArg,
  });

  restoreWindowBounds(win);

  console.log("Window created.");

  return win;
};

const subprocess = isDev ? null : loadPython(openShellArg);

app.whenReady().then(async () => {
  const splashWindow = new BrowserWindow({
    webPreferences: {
      devTools: false,
    },
    icon: path.join(__dirname, "Icon.png"),
    opacity: 1,
    frame: false, // No menu bars nor top bar.
    resizable: false,
    center: true,
    show: false,
    titleBarStyle: "hidden",
    backgroundColor: "#FFF",
    width: 500,
    height: 400,
    alwaysOnTop: true,
  });
  splashWindow.loadFile(path.join(__dirname, "./splash.html"));

  splashWindow.once("ready-to-show", () => {
    splashWindow.show();
  });

  await createEssentialFolders();

  // Must be called before API calls on the main process.
  // (renderer process API calls have a similar function in react.tsx)
  const { remoteAddress } = await readDangerousConfigMain();

  const additionalSources = `http://${remoteAddress}:5000 ws://${remoteAddress}:5100 ws://${remoteAddress}:*`;
  const cspContent = `default-src 'self' 'unsafe-inline' http://127.0.0.1:* http://localhost:* ws://127.0.0.1:* ${additionalSources} filesystem data:`;
  session.defaultSession.webRequest.onHeadersReceived((details, callback) => {
    callback({
      responseHeaders: {
        ...details.responseHeaders,
        "Content-Security-Policy": [cspContent],
      },
    });
  });

  let mainWindow = createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) mainWindow = createWindow();
  });

  // Emit store data changes to client.
  store.onDidAnyChange((s, oldState) => {
    mainWindow.webContents.send(ElectronChannels.EMIT_STORE_DATA, s, oldState);
  });

  // Initialize OCR box managers.
  let boxes = store.get("boxes") as any[];

  if (boxes.length === 0) {
    boxes = getDefaultBoxes();
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
    ...dangerousConfigActions,
  ];
  createGatewayActions(electronState, mainWindow, store, ALL_ACTIONS);

  const server = http.createServer();

  const io = new Server(server, {
    pingTimeout: 100000,
    maxHttpBufferSize: 1e10,
  });
  io.on("connection", (socket) => {
    console.log("Socket connected.");

    // Act as a bridge. Cybersecurity says what?
    socket.onAny((evName, ...args) => {
      // console.log(`Emitting ${evName}`);

      const browWindows: BrowserWindow[] = [
        mainWindow,
        ...electronState.managers.map((x) => x.ocrWindow),
      ];
      for (const win of browWindows) {
        if (win) {
          win.webContents.send(`bridge_${evName}`, ...args);
        }
      }
    });
  });

  server.listen(5100, "0.0.0.0", () => {
    console.log("Experimental WS server listening on port 5100.");
  });

  // API call.
  await initializeModelNames(store.store);

  mainWindow.webContents.on("did-finish-load", () => {
    mainWindow.setOpacity(1);
    mainWindow.focus();
  });

  mainWindow.loadFile(path.join(__dirname, "./index.html"));

  splashWindow.destroy();

  mainWindow.setSkipTaskbar(false);
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    if (!isDev) closePython(subprocess);
    app.quit();
  }
});
