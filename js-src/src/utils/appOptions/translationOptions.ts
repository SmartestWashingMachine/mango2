export const TRANSLATION_OPTIONS = [
  {
    name: "Japanese-2-English Qualia",
    value: "nllb_jq",
    desc: `
    Finetuned for Japanese to English with quality-aware decoding.
    `,
  },
  {
    name: "Japanese-2-English Radical",
    value: "nllb_jqrot",
    desc: `
    Finetuned for Japanese to English with QAD and some other tricks. Slower.
    `,
  },
  {
    name: "Korean-2-English Qualia",
    value: "nllb_ko",
    desc: `
    Finetuned for Korean to English.
    `,
  },
  {
    name: "Chinese-2-English Qualia",
    value: "nllb_zh",
    desc: `
    Finetuned for Chinese to English.
    `,
  },
];
