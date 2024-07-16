type IHistoryText = {
  sourceText: string;
  targetText: string[];
  uuid: string;
  attentions: number[][];
  sourceTokens: string[];
  targetTokens: string[];
  otherTargetTexts: string[];
};

export default IHistoryText;
