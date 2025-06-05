import { makeSocket } from "./makeSocket";
import dangerousConfig from "../dangerousConfig/readDangerousConfigRenderer";

/**
 * This function is called when translating a web page.
 */
export const translateWeb = async (
  weblink: string,
  content_filter: string,
  do_preview: boolean
) => {
  const apiUrl = `http://${dangerousConfig.remoteAddress}:5000/processweb`;

  const output = fetch(apiUrl, {
    method: "POST",
    body: JSON.stringify({
      weblink: weblink,
      content_filter: content_filter,
      do_preview: do_preview,
    }),
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
  });
};

export const pollTranslateWebStatus = (
  itemCb: (targetText: string) => void,
  doneCb: () => void
) =>
  new Promise<void>((resolve) => {
    const socket = makeSocket();

    socket.on("connect", () => {
      resolve();
    });

    socket.on("item_taskweb", (data) => {
      if (data && data.text) {
        itemCb(data.text);
      }
    });

    socket.on("done_taskweb", (data) => {
      if (data && data.text) {
        itemCb(data.text);
      }

      doneCb();

      socket.disconnect();
    });
  });
