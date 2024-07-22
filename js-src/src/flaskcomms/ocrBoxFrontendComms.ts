import { makeSocket } from "./makeSocket";

export const listenTask3Updates = (
  boxId: string,
  beginCb: () => void,
  doneCb: (sourceText: string[], targetText: string[]) => void,
  streamCb?: (targetText: string) => void,
  connectCb?: () => void,
  disconnectCb?: () => void,
) => {
  const socket = makeSocket({ transports: ["websocket"], upgrade: false, }); // Disable long polling fallback, as SocketIO does not force a re-upgrade on failure.

  socket.on('connect', () => {
    if (!connectCb) return;
    connectCb();
  });

  socket.on('disconnect', () => {
    if (!disconnectCb) return;
    disconnectCb();
  });

  socket.on("begin_translating_task3", (data) => {
    if (!data || data.boxId !== boxId) return;

    beginCb();
  });

  // In case of clipboard updates.
  socket.on("begin_translating_task2", (data) => {
    if (!data || data.boxId !== boxId) return;

    beginCb();
  });

  // Called when task3 is done only.
  socket.on("item_task3", (data) => {
    if (!data || !data.text) {
      doneCb([], []);
    } else if (data.boxId == boxId) {
      doneCb(data.text, data.sourceText);
      const w = window as any;

      if (data.text && data.text.length > 0) {
        // Attention not yet supported for task3. was TODO... but we don't support attention anymore. Not worth maintaining.
        w.electronAPI.addToTextHistory([data.text], data.sourceText);
      }
    }
  });

  // Called whenever a new token is streamed. Only when useStream is enabled for a box.
  socket.on("item_stream", (data) => {
    if (!streamCb) return;

    if (!data || !data.text) {
      streamCb("");
    } else if (data.boxId == boxId) {
      streamCb(data.text);
    }
  });

  // This is used when the clipboard listening flag is on. Called when task2 is done only.
  socket.on("done_translating_task2", (data) => {
    if (!data || !data.text) {
      doneCb([], []);
    } else if (data.boxId == boxId) {
      doneCb(data.text, data.sourceText);
      const w = window as any;

      // Ids is null, so it's made on the function later on.
      w.electronAPI.addToTextHistory([data.text], [data.sourceText], null);
    }
  });

  return socket;
};
