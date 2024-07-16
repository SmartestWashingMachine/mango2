import { reshapeFilesAsRoot } from "./reshapeFilesAsRoot";
import { APP_LIBRARY_PATH, APP_CSV_PATH } from "../../constants";
import { retrieveFilesInFolder } from "./retrieveFilesInFolder";

/**
 * Retrieve all files in the library folder.
 */
export const retrieveFilesInLibrary = async (retrieveMode = "images") => {
  try {
    const folderPath = retrieveMode === "csv" ? APP_CSV_PATH : APP_LIBRARY_PATH;
    const files = await retrieveFilesInFolder(folderPath);
    return reshapeFilesAsRoot(folderPath, files);
  } catch (err) {
    console.log(err);
    return;
  }
};
