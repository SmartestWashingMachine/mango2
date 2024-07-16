import fs from "fs/promises";
import {
  APP_LIBRARY_PATH,
  APP_CSV_PATH,
  APP_FONTS_PATH,
} from "../../constants";

export const createEssentialFolders = async () => {
  // Create folders if not existing.
  await fs.mkdir(APP_CSV_PATH, { recursive: true });
  await fs.mkdir(APP_LIBRARY_PATH, { recursive: true });
  await fs.mkdir(APP_FONTS_PATH, { recursive: true });
};
