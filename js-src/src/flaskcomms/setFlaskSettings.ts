import nodeFetch from "node-fetch";
import { IStoreClientToServer } from "../types/ElectronStore";
import dangerousConfig from "../dangerousConfig/readDangerousConfigMain";

const timeout = (ms: number) => {
  return new Promise((resolve) => setTimeout(resolve, ms));
};

/**
 * Called once when the app initially loads. Since all settings are saved on the electron client, every app load we update it on the server.
 * CALLED BY ELECTRON MAIN PROCESS.
 *
 * We also call it when some settings change.
 */
export const initializeModelNames = async (data: IStoreClientToServer) => {
  // Update the local backend config for certain variables (like capturing the window).
  if (dangerousConfig.remoteAddress !== "127.0.0.1") {
    await updateConfigInBackend(data, "127.0.0.1");
  }

  await updateConfigInBackend(data, dangerousConfig.remoteAddress);
};

const updateConfigInBackend = async (
  data: IStoreClientToServer,
  ip: string
) => {
  const apiUrl = `http://${ip}:5000/switchmodels`;

  const formData = JSON.stringify({
    ...data,
  });

  try {
    const output = await nodeFetch(apiUrl, {
      method: "POST",
      body: formData,
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
    });

    if (output.status !== 200) throw Error("Invalid status code.");
  } catch (err) {
    await timeout(5000);
    await initializeModelNames(data);
  }
};
