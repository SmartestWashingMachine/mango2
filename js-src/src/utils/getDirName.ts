export const getDirName = (path: string) => {
  try {
    const pathComponents = path.split("\\");
    return pathComponents[pathComponents.length - 2];
  } catch {
    return "";
  }
};
