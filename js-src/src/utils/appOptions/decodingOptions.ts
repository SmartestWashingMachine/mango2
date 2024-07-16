export const DECODING_OPTIONS = [
  {
    name: "MAP Beam Decoding",
    value: "beam",
    desc: `
    Fast. The best translation is given according to the
    translation model's predicted probabilities only.
    `,
  },
  {
    name: "MBR Sampling",
    value: "mbr_gsample",
    desc: `
    While translating, the model may randomly decide to pick less
    "optimal" words. A reranking model will score and find the
    best full translation.
    `,
  },
  {
    name: "MBR Beam Sampling",
    value: "mbr_bsample",
    desc: `
    GLITCHY - Way slower but might give more sensible
    outputs. Using this is almost always a bad idea.
    `,
  },
];
