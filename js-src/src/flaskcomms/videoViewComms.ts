import { makeSocket } from "./makeSocket";
import dangerousConfig from "../dangerousConfig/readDangerousConfigRenderer";

export const translateVideo = async (
  file: any, // path string
  mode: string
) => {
  const taskEndpoint = mode === "visual" ? "processtask5" : "processtask9";
  const apiUrl = `http://${dangerousConfig.remoteAddress}:5000/${taskEndpoint}`;

  const formData = new FormData() as any;
  formData.append("videoFilePath", file);

  const output = fetch(apiUrl, {
    method: "POST",
    body: formData,
    headers: {
      Accept: "application/json",
    },
  });
};

export const pollTranslateVideoStatus = (
  progressCb: (progress: number) => void,
  doneCb: (outPath: string) => void
) =>
  new Promise<void>((resolve) => {
    const socket = makeSocket();

    socket.on("connect", () => {
      resolve();
    });

    socket.on("progress_task5", (data?: any) => {
      if (!data) return;

      progressCb(data || 0);
    });

    socket.on("done_translating_task5", (data: string) => {
      doneCb(data);

      socket.disconnect();
    });
  });

export const checkFfmpegInstalled = async () => {
  const apiUrl = `http://${dangerousConfig.remoteAddress}:5000/ffmpeginstalled`;

  const output = await fetch(apiUrl, {
    method: "GET",
    headers: {
      Accept: "application/json",
    },
  });

  if (output.status !== 200) throw Error("Invalid status code.");

  return output.json();
};
