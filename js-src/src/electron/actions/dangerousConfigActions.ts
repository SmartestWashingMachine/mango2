import fs from "fs/promises";
import ElectronCommands from "../../types/ElectronCommands";
import { GatewayAction } from "../../types/GatewayAction";
import { APP_DANGEROUS_CONFIG_FILE } from "../../constants";

const readOrCreateJson = async (filePath: string, defaultData: any) => {
  try {
    await fs.access(filePath, fs.constants.F_OK);
    const data = await fs.readFile(filePath, "utf-8");
    return JSON.parse(data);
  } catch (error) {
    await fs.writeFile(filePath, JSON.stringify(defaultData, null, 4), "utf-8");
    return defaultData;
  }
};

export const readDangerousConfig = async () => {
  const parsed = await readOrCreateJson(APP_DANGEROUS_CONFIG_FILE, {
    remoteAddress: "127.0.0.1",
  });

  return parsed;
};

const readDangerousConfigAction: GatewayAction = {
  command: ElectronCommands.READ_DANGEROUS_CONFIG,
  commandType: "handle",
  fn: async (e, w, s, store) => {
    const data = await readDangerousConfig();

    console.log("Dangerous config data read. Address:");
    console.log(data.remoteAddress);

    return data;
  },
};

export default [readDangerousConfigAction];
