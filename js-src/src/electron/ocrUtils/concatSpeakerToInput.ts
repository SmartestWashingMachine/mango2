export type ConcatSpeakerToInputOpts = {
  text: string;
  /* A callback that returns a string containing the speaker name. */
  speakerCallback: () => Promise<string | null>;
};

export const concatSpeakerToInput = async (opts: ConcatSpeakerToInputOpts) => {
  const speakerInfo = await opts.speakerCallback();

  const hasSpeakerInfo = speakerInfo && speakerInfo.length > 0;
  const textToTranslate = hasSpeakerInfo
    ? `[${speakerInfo}]: ${opts.text}`
    : opts.text;

  return textToTranslate;
};
