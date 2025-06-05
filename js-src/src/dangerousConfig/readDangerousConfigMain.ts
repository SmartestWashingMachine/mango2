import { readDangerousConfig } from "../electron/actions/dangerousConfigActions";

let dangerousConfig: any = {};

export const readDangerousConfigMain = async () => {
  const newConfig = await readDangerousConfig();

  // Need to mutate the object directly.
  for (const key in newConfig) {
    dangerousConfig[key] = newConfig[key];
  }
};

export default dangerousConfig;
