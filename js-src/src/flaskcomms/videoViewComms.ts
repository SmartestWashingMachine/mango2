import { makeSocket } from "./makeSocket";
import dangerousConfig from "../dangerousConfig/readDangerousConfigRenderer";

export const translateVideo = async (
  file: any // path string
) => {
  const apiUrl = `http://${dangerousConfig.remoteAddress}:5000/processtask5`;

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
