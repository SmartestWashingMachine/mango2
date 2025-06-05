import { makeSocket } from "./makeSocket";
import dangerousConfig from "../dangerousConfig/readDangerousConfigRenderer";

const buildConstraints = (constraints: string) => {
  // Each word becomes a separate constraint. Words in double quotes are treated as a phrase (single constraint).
  // E.G: dog funny very == 3 constraints (dog, funny, very).
  // E.G: cat "is strange" yes and == 4 constraints (cat, is strange, yes, and).

  const parsed = []; // The actual list of constraints to send to the backend.

  const regex = /("[^"]+")/g; // Find all characters in the double quotes.
  const matches = constraints.match(regex); // Each match will start and end with double quotes.
  if (matches) {
    const cleaned = matches
      .map((s) => s.slice(1, s.length - 1))
      .filter((s) => s.length > 0);
    parsed.push(...cleaned);
  }

  const remainingConstraints = constraints.replaceAll(regex, "");
  const words = remainingConstraints
    .split(" ")
    .filter((w) => w.trim().length > 0);

  parsed.push(...words);
  return parsed;
};

export const translateText = async (
  text: string,
  constraints: string | null,
  tgtContextMemory: string | null
) => {
  const apiUrl = `http://${dangerousConfig.remoteAddress}:5000/processtask2`;

  const body: any = { text };

  if (constraints) {
    body["required_words"] = buildConstraints(constraints);
  }

  if (tgtContextMemory) {
    body["tgt_context_memory"] = tgtContextMemory;
  }

  // TODO: Make this configurable since it affects performance ever so slightly.
  body["output_attentions"] = true;

  const output = fetch(apiUrl, {
    method: "POST",
    body: JSON.stringify(body),
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
  });
};

export const pollTranslateTextStatus = (
  progressCb: (progress: number) => void,
  itemCb: (sourceText: string, targetText: string) => void,
  doneCb: () => void
) =>
  new Promise<void>((resolve) => {
    const socket = makeSocket();

    socket.on("connect", () => {
      resolve();
    });

    socket.on("progress_task2", (progressFrac: number) => {
      progressCb(progressFrac || 0);
    });

    socket.on("done_translating_task2", (data) => {
      if (data && data.text && data.sourceText) {
        itemCb(data.sourceText, data.text);
      }

      doneCb();

      socket.disconnect();
    });
  });

export const pollGenericTranslateStatus = (
  streamCb: (genericId: string, sourceText: string, text: string) => void
) => {
  const socket = makeSocket();

  const cleanupFn = () => {
    try {
      socket.disconnect();
    } catch {
      console.log("Failed to disconnect generic translate socket.");
    }
  };

  socket.on("item_stream", (data) => {
    if (!streamCb) return;

    // The genericId is the key here - it tells us that this is a generic translation task (not one related to an OCR box).
    if (!data || !data.genericId || !data.text || !data.sourceText) return;

    streamCb(data.genericId, data.sourceText, data.text);
  });

  return cleanupFn;
};
