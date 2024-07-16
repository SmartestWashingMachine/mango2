import { makeSocket } from "./makeSocket";

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
  const apiUrl = "http://localhost:5000/processtask2";

  const body: any = { text };

  if (constraints) {
    body["required_words"] = buildConstraints(constraints);
  }

  if (tgtContextMemory) {
    body["tgt_context_memory"] = tgtContextMemory;
  }

  // TODO: Make this configurable since it affects performance ever so slightly.
  body["output_attentions"] = true;

  const output = await fetch(apiUrl, {
    method: "POST",
    body: JSON.stringify(body),
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
  });
  if (output.status !== 202) throw Error("Invalid status code.");
  if (!output.ok) {
    console.log("Failed fetch:");
    console.log(output.status);
    console.log(output.statusText);
  }
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
