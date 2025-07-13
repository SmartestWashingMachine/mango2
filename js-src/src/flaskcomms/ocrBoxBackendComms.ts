import nodeFetch, { FormData } from "node-fetch";
import { Blob } from "buffer";
import dangerousConfig from "../dangerousConfig/readDangerousConfigMain";

/**
 * This function is called when translating by simply pressing the scanning key. CALLED FROM ELECTRON CURRENTLY.
 */
export const translateImageGiveText = async (
  files: Buffer[],
  boxId: string,
  textDetect: boolean,
  tgtContextMemory: string | null,
  streamOutput: boolean | null,
  translateLinesIndividually: number = 0
) => {
  const apiUrl = `http://${dangerousConfig.remoteAddress}:5000/processtask3`;

  const formData = new FormData();
  for (const f of files) {
    const blob = new Blob([f]);
    formData.append("file", blob as any);
  }

  if (tgtContextMemory !== null) {
    formData.append("tgt_context_memory", tgtContextMemory);
  }

  if (streamOutput) formData.append("useStream", streamOutput ? "on" : "off");

  formData.append("boxId", boxId);
  formData.append("textDetect", textDetect ? "on" : "off");

  formData.append(
    "translateLinesIndividually",
    translateLinesIndividually.toString()
  );

  const output = await nodeFetch(apiUrl, {
    method: "POST",
    body: formData,
    headers: {
      Accept: "application/json",
    },
  });
  if (output.status !== 202) throw Error("Invalid status code.");
};

/**
 * This function is called when translating by simply pressing the scanning key with the "Faster Capture" option enabled. CALLED FROM ELECTRON CURRENTLY.
 */
export const translateImageGiveTextFaster = async (
  coords: number[],
  boxId: string,
  textDetect: boolean,
  tgtContextMemory: string | null,
  streamOutput: boolean | null,
  translateLinesIndividually: number = 0
) => {
  // This always goes to local host first - the backend there will then push it to the remote backend.
  const apiUrl = `http://localhost:5000/processtask3new`;

  const formData = new FormData();
  for (const f of coords) {
    formData.append("coords", f.toString());
  }
  formData.append("x1", coords[0].toString());
  formData.append("y1", coords[1].toString());
  formData.append("width", coords[2].toString());
  formData.append("height", coords[3].toString());

  if (tgtContextMemory !== null) {
    formData.append("tgt_context_memory", tgtContextMemory);
  }

  if (streamOutput) formData.append("useStream", streamOutput ? "on" : "off");

  formData.append("boxId", boxId);
  formData.append("textDetect", textDetect ? "on" : "off");

  formData.append(
    "translateLinesIndividually",
    translateLinesIndividually.toString()
  );

  const output = await nodeFetch(apiUrl, {
    method: "POST",
    body: formData,
    headers: {
      Accept: "application/json",
    },
  });
  if (output.status !== 202) throw Error("Invalid status code.");
};

/**
 * This function is called when translating by detecting changes in the clipboard. CALLED FROM ELECTRON CURRENTLY.
 */
export const translateTextGiveText = async (
  text: string,
  boxId: string,
  tgtContextMemory: string | null,
  useStream: boolean | null
) => {
  const apiUrl = `http://${dangerousConfig.remoteAddress}:5000/processtask2`;

  const formData = { text, boxId, useStream } as any;

  if (tgtContextMemory) {
    formData["tgt_context_memory"] = tgtContextMemory;
  }

  // TODO: Make this configurable since it affects performance ever so slightly.
  formData["output_attentions"] = true;

  const output = await nodeFetch(apiUrl, {
    method: "POST",
    body: JSON.stringify(formData),
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
  });
  if (output.status !== 202) throw Error("Invalid status code.");
};

/**
 * This function is called when refining a translation when the user makes a request. CALLED FROM ELECTRON CURRENTLY.
 */
export const refineTranslation = async (
  sourceText: string,
  targetText: string,
  boxId: string,
  useStream: boolean | null
) => {
  const apiUrl = `http://${dangerousConfig.remoteAddress}:5000/processtask6`;

  const formData = { sourceText, targetText, boxId, useStream } as any;

  const output = await nodeFetch(apiUrl, {
    method: "POST",
    body: JSON.stringify(formData),
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
  });
  if (output.status !== 202) throw Error("Invalid status code.");
};

/**
 * This function is called when translating speaker box contents. No websocket needed. CALLED FROM ELECTRON CURRENTLY.
 *
 * Does NOT translate.
 */
export const scanImageGiveText = async (
  files: Buffer[],
  boxId: string,
  textDetect: boolean,
  tgtContextMemory: string | null
) => {
  const apiUrl = `http://${dangerousConfig.remoteAddress}:5000/processtask4`;

  const formData = new FormData();
  for (const f of files) {
    const blob = new Blob([f]);
    formData.append("file", blob as any);
  }

  // tgtContextMemory is unused - there's no translation going on after all.
  formData.append("boxId", boxId);
  formData.append("textDetect", textDetect ? "on" : "off");

  const output = await nodeFetch(apiUrl, {
    method: "POST",
    body: formData,
    headers: {
      Accept: "application/json",
    },
  });
  if (output.status !== 202) throw Error("Invalid status code.");

  const data: any = await output.json();
  return data?.text;
};

export const triggerEnterNodeFetch = async () => {
  console.log("Requesting ENTER key press from Python backend.");

  const apiUrl = `http://${dangerousConfig.remoteAddress}:5000/triggerenter`;

  await nodeFetch(apiUrl, {
    method: "GET",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
  });
};

// All params here should be snake cased not camelCase.
export const rememberBoxActivationData = async (boxData: any) => {
  // This always goes to local host first - the backend there will then push it to the remote backend.
  const apiUrl = `http://localhost:5000/task3rememberbox`;

  await nodeFetch(apiUrl, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      boxState: {
        ...boxData,
        x1: [boxData.x1],
        y1: [boxData.y1],
        width: [boxData.width],
        height: [boxData.height],
      },
    }),
  });
};

export const forgetBoxActivationData = async (boxId: any, thisBoxId: any) => {
  // This always goes to local host first - the backend there will then push it to the remote backend.
  const apiUrl = `http://localhost:5000/task3forgetbox`;

  await nodeFetch(apiUrl, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ box_id: boxId, this_box_id: thisBoxId }),
  });
};
