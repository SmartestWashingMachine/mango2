type IReplaceTerm = {
  /** The original word to replace. */
  original: string;
  /** The word to replace it with. */
  replacement: string;
  /** If "source", then do these checks and replacements on the source language (the input sentence). Otherwise, perform them on the target language (the output sentence). */
  onSide: string;
  uuid: string;
  enabled: boolean;
};

export default IReplaceTerm;
