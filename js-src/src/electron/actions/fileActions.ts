import fs from "fs/promises";
import path from "path";
import {
  APP_LIBRARY_PATH,
  APP_CSV_PATH,
  APP_FONTS_PATH,
  APP_MODELS_PATH,
  DOWNLOADS_PATH,
  APP_LOGS_PATH,
  APP_CACHE_FOLDER,
} from "../../constants";
import ElectronChannels from "../../types/ElectronChannels";
import ElectronCommands from "../../types/ElectronCommands";
import { v4 as uuidv4 } from "uuid";
import { GatewayAction } from "../../types/GatewayAction";
import { getI, saveBase64Images } from "../fileUtils/saveBase64Image";
import { retrieveFilesInLibrary } from "../fileUtils/retrieveFilesInLibrary";
import { retrieveFilesInFolder } from "../fileUtils/retrieveFilesInFolder";
import { shell, dialog } from "electron";
import { initializeModelNames } from "../../flaskcomms/setFlaskSettings";

const retrieveFilesAction: GatewayAction = {
  command: ElectronCommands.RETRIEVE_FILES,
  commandType: "handle",
  fn: async (e, _, __, ___, retrieveMode: string) => {
    // Retrieve all files from the library folder.
    const files = await retrieveFilesInLibrary(retrieveMode);

    return files;
  },
};

const onCreateFile: GatewayAction = {
  command: ElectronCommands.CREATE_FILE,
  commandType: "on",
  fn: async (e, _, __, ___, filePath: string) => {
    await fs.mkdir(filePath, { recursive: true });

    const files = await retrieveFilesInLibrary();

    e.sender.send(ElectronChannels.DONE_RETRIEVING_FILES, files);
    e.sender.send(ElectronChannels.DONE_CREATING_FILE);
  },
};

const processFilesAction: GatewayAction = {
  command: ElectronCommands.PROCESS_FILES,
  commandType: "handle",
  fn: async (e, _, __, ___, files, folderName, fileName, annotations) => {
    // Mainly called from ImageView when saving one.

    const { folderPath } = await saveBase64Images(
      files,
      folderName,
      fileName,
      annotations
    );

    const foundFiles = await retrieveFilesInLibrary();
    //const filesInFolder = await retrieveFilesInFolder(folderPath);
    return {
      rootItem: foundFiles,
      //imagePaths: filesInFolder.map((x) => x.fullPath),
      folderPath,
    };
  },
};

const saveCsvFileAction: GatewayAction = {
  command: ElectronCommands.SAVE_CSV_FILE,
  commandType: "handle",
  fn: async (e, _, __, ___, csvRows: string[][], columnNames: string[]) => {
    // columnNames is unused for now. TODO
    const newFileName = path.join(APP_CSV_PATH, `${uuidv4()}.json`);

    console.log(`Saving backlog as: ${newFileName}`);

    const dataToJson: any[] = [];
    for (const c of csvRows) {
      dataToJson.push({ SourceText: c[0], TargetText: c[1][0] });
    }

    const data = JSON.stringify(dataToJson, null, 4);
    try {
      await fs.writeFile(newFileName, data);
    } catch (err) {
      console.log(`ERROR: ${err}`);
    }

    return newFileName;
  },
};

const openAmgAction: GatewayAction = {
  command: ElectronCommands.OPEN_AMG,
  commandType: "handle",
  fn: async (e, _, __, ___, fullPath: string) => {
    const data = await fs.readFile(fullPath, "utf-8");
    const parsed = JSON.parse(data);

    return parsed;
  },
};

const saveImageAction: GatewayAction = {
  command: ElectronCommands.SAVE_IMAGE,
  commandType: "handle",
  fn: async (e, _, __, ___, folderName, imageBlob) => {
    const folderPath = path.join(APP_LIBRARY_PATH, folderName);
    const i = await getI(folderPath);

    const newFullPath = path.resolve(APP_LIBRARY_PATH, folderName, `${i}.png`);

    await fs.writeFile(newFullPath, imageBlob, "base64");

    const foundFiles = await retrieveFilesInLibrary();
    return { rootItem: foundFiles };
  },
};

const retrieveFontsAction: GatewayAction = {
  command: ElectronCommands.RETRIEVE_FONT_FILES,
  commandType: "handle",
  fn: async () => {
    const dir = await fs.readdir(APP_FONTS_PATH, { withFileTypes: true });
    const files = await Promise.all(dir.map(async (file) => file.name));

    return {
      fontNames: files,
      fontPaths: files.map(
        (s) => `${APP_FONTS_PATH.replaceAll("\\", "/")}/${s}`
      ),
    };
  },
};

const showFileAction: GatewayAction = {
  command: ElectronCommands.SHOW_FILE,
  commandType: "handle",
  fn: async (e, _, __, ___, fullPath) => {
    // Only show items in library folder.
    const rel = path.relative(APP_LIBRARY_PATH, fullPath);

    if (rel && !rel.startsWith("..") && !path.isAbsolute(rel))
      shell.showItemInFolder(fullPath);
  },
};

const openModelsAction: GatewayAction = {
  command: ElectronCommands.OPEN_MODELS_FOLDER,
  commandType: "handle",
  fn: async () => {
    shell.showItemInFolder(APP_MODELS_PATH);
  },
};

const openFontsAction: GatewayAction = {
  command: ElectronCommands.OPEN_FONTS_FOLDER,
  commandType: "handle",
  fn: async () => {
    shell.showItemInFolder(APP_FONTS_PATH);
  },
};

const openLogsFolder: GatewayAction = {
  command: ElectronCommands.OPEN_LOGS_FOLDER,
  commandType: "handle",
  fn: async () => {
    shell.showItemInFolder(APP_LOGS_PATH);
  },
};

const openCacheFolder: GatewayAction = {
  command: ElectronCommands.OPEN_CACHE_FOLDER,
  commandType: "handle",
  fn: async () => {
    shell.showItemInFolder(APP_CACHE_FOLDER);
  },
};

const importTermsAction: GatewayAction = {
  command: ElectronCommands.IMPORT_TERMS,
  commandType: "handle",
  fn: async (e, win, state, store) => {
    const terms = store.get("terms");

    const result = await dialog.showOpenDialog({
      defaultPath: DOWNLOADS_PATH,
      properties: ["openFile"],
    });
    if (result.canceled || !result.filePaths || result.filePaths.length === 0)
      return;

    try {
      const data = await fs.readFile(result.filePaths[0]);
      const jsonData = JSON.parse(data.toString());

      console.log(`Importing terms as: ${result.filePaths[0]}`);
      store.set("terms", jsonData);

      await initializeModelNames(store.store);
    } catch (err) {
      console.log(err);
      return;
    }
  },
};

const exportTermsAction: GatewayAction = {
  command: ElectronCommands.EXPORT_TERMS,
  commandType: "handle",
  fn: async (e, win, state, store) => {
    const terms = store.get("terms");

    const result = await dialog.showSaveDialog({ defaultPath: DOWNLOADS_PATH });
    if (result.canceled || !result.filePath) return;

    console.log(`Exporting terms as: ${result.filePath}`);

    // Map to JSON
    const data = JSON.stringify(terms, null, 4);
    try {
      await fs.writeFile(result.filePath, data);
    } catch (err) {
      console.log(`ERROR: ${err}`);
    }
  },
};

export default [
  retrieveFilesAction,
  onCreateFile,
  processFilesAction,
  saveCsvFileAction,
  openAmgAction,
  saveImageAction,
  retrieveFontsAction,
  showFileAction,
  openModelsAction,
  openFontsAction,
  openLogsFolder,
  importTermsAction,
  exportTermsAction,
  openCacheFolder,
];
