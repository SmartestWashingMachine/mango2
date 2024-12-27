export const TRANSLATION_OPTIONS = [
  {
    name: "Japanese-2-English Qualia",
    value: "nllb_jq",
    desc: `
    Finetuned for Japanese to English with quality-aware decoding.
    `,
  },
  {
    name: "Japanese-2-English Qualia 300",
    value: "nllb_jq300",
    desc: `
    A better variant of Japanese-2-English Qualia.
    `,
  },
  /* A mistake! Rotary positional embeddings seem to be a poor fit for "medium"-sized translation models. Why do T5 positional embeddings work so well?? {
    name: "Japanese-2-English Radical",
    value: "nllb_jqrot",
    desc: `
    Finetuned for Japanese to English with QAD and some other tricks. Slightly slower.
    `,
  }, */
  {
    // Little dev note: I'm still not satisfied with the idea of this model. It's massive, and yet it still uses absolute positional embeddings? Sure, it seems to be competitive with those LLama variants, but that's not a hard feat to achieve.
    // The fact that the model generalizes well with adapters is interesting though. That would seem to imply that my dataset isn't as diverse as I'd like.
    // Additional dev note: New project makes this model do well. Very interesting.
    name: "Japanese-2-English Madness",
    value: "nllb_jmad",
    desc: `
    The strongest. Incredibly slow.
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
  {
    name: "Korean-2-English Madness",
    value: "nllb_komad",
    desc: `
    Incredibly slow.
    `,
  },
  {
    name: "Chinese-2-English Madness",
    value: "nllb_zhmad",
    desc: `
    Incredibly slow.
    `,
  },
];
