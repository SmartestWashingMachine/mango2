export const SPELLING_CORRECTION_OPTIONS = [
  {
    name: "None",
    value: "default",
    desc: `
    Fastest. Spelling correction shouldn't be necessary in most cases.
    `,
  },
  {
    name: "Goliath Remix",
    value: "remix",
    desc: `
    An extremely large model for refining translations. Incredibly slow. Will use the GPU with the same settings as the translation model.
    `,
  },
];
