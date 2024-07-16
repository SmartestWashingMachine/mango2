import nodeFetch from "node-fetch";
import { IStoreClientToServer } from "../types/ElectronStore";

const timeout = (ms: number) => {
  return new Promise((resolve) => setTimeout(resolve, ms));
};

/**
 * Called once when the app initially loads. Since all settings are saved on the electron client, every app load we update it on the server.
 */
export const initializeModelNames = async (data: IStoreClientToServer) => {
  const apiUrl = "http://localhost:5000/switchmodels";

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
