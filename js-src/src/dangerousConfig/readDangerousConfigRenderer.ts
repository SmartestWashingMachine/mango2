import { MainGateway } from "../utils/mainGateway";

type DangerousConfig = {
  remoteAddress?: string;
};

let dangerousConfig: DangerousConfig = {};

export const readDangerousConfigRenderer = async () => {
  const newConfig = await MainGateway.readDangerousConfig();

  // Need to mutate the object directly.
  for (const key in newConfig) {
    dangerousConfig[key as keyof DangerousConfig] = newConfig[key];
  }
};

export default dangerousConfig;
