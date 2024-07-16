export const pTransformerJoin = (inputTexts: string[]) => {
  if (inputTexts.length === 1) return `${inputTexts[0]}`;

  const others = inputTexts.slice(0, inputTexts.length - 1);
  const cur = inputTexts[inputTexts.length - 1];

  return `${others.join("<SEP>")}<TSOS>${cur}`.trim();
};
