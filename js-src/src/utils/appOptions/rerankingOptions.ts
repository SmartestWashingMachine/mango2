export const RERANKING_OPTIONS = [
  {
    name: "None",
    value: "none",
    desc: `
    Fast. No reranking will take place.
    `,
  },
  {
    name: "List Energy",
    value: "listenergy_nocontext",
    desc: `
    Attempts to approximate chrF++ scores and find the best
    scoring candidate. Does not use context to determine the best
    candidate but is quite fast.
    `,
  },
  {
    name: "Doctor",
    value: "doctor",
    desc: `
    Attempts to approximate chrF++ scores and find the best
    scoring candidate. Can use context.
    `,
  },
  {
    name: "Human",
    value: "human",
    desc: `
    Attempts to find the translation candidate that appears the
    least like a machine translation output. Can use context.
    `,
  },
  {
    name: "Quality",
    value: "quality",
    desc: `
    Attempts to find the translation candidate that has the highest
    "quality". Does not use context but this model supports
    Chinese and (sometimes) Korean too.
    `,
  },
];
