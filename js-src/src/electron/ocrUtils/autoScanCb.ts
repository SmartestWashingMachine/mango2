import { translateImageGiveText } from "../../flaskcomms/ocrBoxBackendComms";
import { imagesDifferent } from "./imagesDifferent";

export type AutoScanCbOpts = {
  cloakBox: () => void;
  revealBox: () => void;
  takeImage: () => Promise<{ finalImgBuffer: Buffer } | undefined | null>;
  prevImage: Buffer | null;
  boxId: string;
  textDetect: boolean;
  useStream: boolean;
  paused: boolean | null | undefined;
};

export const autoScanCb = async (opts: AutoScanCbOpts) => {
  opts.cloakBox();

  const result = await opts.takeImage();
  opts.revealBox();
  if (!result) {
    return;
  }

  const isDiff =
    opts.prevImage !== null
      ? await imagesDifferent(opts.prevImage, result.finalImgBuffer)
      : true;

  if (isDiff) {
    // Speaker callback is not supported here yet. TODO.
    if (!opts.paused)
      await translateImageGiveText(
        [result.finalImgBuffer],
        opts.boxId,
        opts.textDetect,
        null,
        opts.useStream
      );

    return result.finalImgBuffer;
  }
};
