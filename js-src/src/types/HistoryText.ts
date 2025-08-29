type IHistoryText = {
  sourceText: string;
  targetText: string[];
  uuid: string;
  attentions: number[][];
  sourceTokens: string[];
  targetTokens: string[];
  otherTargetTexts: string[];
};

// For auto-detected names. These can show up in the TextView i.e: when playing games.
export type INameItem = Partial<IHistoryText> & {
  source: string;
  target: string;
  gender: string;
  uuid: string;
};

export default IHistoryText;
