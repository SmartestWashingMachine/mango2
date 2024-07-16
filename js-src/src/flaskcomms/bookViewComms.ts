import { makeSocket } from "./makeSocket";

export const translateBook = async (
  file: any,
  tgtContextMemory: string | null
) => {
  const apiUrl = "http://localhost:5000/processbookb64";

  const formData = new FormData() as any;
  formData.append("file", file);

  if (tgtContextMemory !== null) {
    formData.append("tgt_context_memory", tgtContextMemory);
  }

  const output = await fetch(apiUrl, {
    method: "POST",
    body: formData,
    headers: {
      Accept: "application/json",
    },
  });
  if (output.status !== 202) throw Error("Invalid status code.");
};

export const pollTranslateBookStatus = (
  progressCb: (progress: number, sentsDone: number, sentsTotal: number) => void,
  doneCb: () => void
) =>
  new Promise<void>((resolve) => {
    const socket = makeSocket();

    socket.on("connect", () => {
      resolve();
    });

    socket.on("progress_epub", (data?: any) => {
      if (!data) return;

      progressCb(data.progressFrac || 0, data.sentsDone, data.sentsTotal);
    });

    socket.on("done_translating_epub", (data) => {
      doneCb();

      socket.disconnect();
    });
  });
