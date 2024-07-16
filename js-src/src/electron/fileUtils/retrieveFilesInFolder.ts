import fs from "fs/promises";
import path from "path";
import { ExtendedFileInfo } from "../../types/FileInfo";

export const retrieveFilesInFolder = async (dirPath: string) => {
  const dir = await fs.readdir(dirPath, { withFileTypes: true });

  const files = await Promise.all(
    dir.map(async (file) => {
      const fullPath = path.resolve(dirPath, file.name);

      const childrenItems = file.isDirectory()
        ? await retrieveFilesInFolder(fullPath)
        : [];

      const itemStats = await fs.stat(fullPath);

      const item: ExtendedFileInfo = {
        fullPath,
        fileName: file.name,
        childrenItems,
        createdDate: itemStats.mtime.getTime(),
      };

      return item;
    })
  );

  const sortByDates = (a: ExtendedFileInfo, b: ExtendedFileInfo) =>
    b.createdDate - a.createdDate;

  // Sort folders so that newest files are first in the list, and folders are prioritized.
  const folders = files
    .filter((f) => f.childrenItems.length > 0)
    .sort(sortByDates);

  // Newer files come LAST.
  const nonFolders = files
    .filter((f) => f.childrenItems.length === 0)
    .sort((a, b) => sortByDates(b, a));

  return [...folders, ...nonFolders];
};
