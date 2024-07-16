import { FileInfo } from "../../types/FileInfo";
import path from "path";

export const reshapeFilesAsRoot = (dirPath: string, files: FileInfo[]) => {
  const f: FileInfo = {
    fileName: path.basename(dirPath),
    fullPath: dirPath,
    childrenItems: files,
  };

  return f;
};
