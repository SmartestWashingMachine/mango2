import { clipboard } from "electron";
import { concatSpeakerToInput } from "./concatSpeakerToInput";
import { translateTextGiveText } from "../../flaskcomms/ocrBoxBackendComms";

type ClipboardCbOpts = {
  prevText: string | null | undefined;
  paused: boolean | null | undefined;
  speakerCallback: () => Promise<string | null>; // Retrieve speaker feedback if needed.
  boxId: string;
  useStream: boolean;
};

export const getTextFromClipboard = (opts: ClipboardCbOpts) => {
  const text = clipboard.readText();

  if (opts.prevText === text || opts.paused) return [text, false];

  // If this check isn't performed, then it'll process as soon as the box app opens... which is what we want now!
  // if (opts.prevText === null) return [text, false];

  // As a safety precaution, the user might accidently open the window beforehand with an extremely long text copied.
  // Since this route is intended for capturing short texts in games or other media, we just cancel requests with an absurdly long length.
  if (!text || text.trim().length === 0 || text.length >= 10000)
    return [opts.prevText, false];

  return [text, true] as any;
};

export const clipboardCb = async (text: string, opts: ClipboardCbOpts) => {
  const textToTranslate = await concatSpeakerToInput({
    text,
    speakerCallback: opts.speakerCallback,
  });

  // The backend will emit the result via a websocket to the client.
  await translateTextGiveText(
    textToTranslate,
    opts.boxId,
    null,
    opts.useStream
  );
};
