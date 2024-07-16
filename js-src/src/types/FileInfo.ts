// Used for images.
export type FileInfo = {
  fileName: string;
  fullPath: string;
  childrenItems: FileInfo[];
};

export type ExtendedFileInfo = FileInfo & {
  createdDate: number;
};

export default FileInfo;
