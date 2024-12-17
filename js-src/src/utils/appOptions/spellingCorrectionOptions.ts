export const SPELLING_CORRECTION_OPTIONS = [
  {
    name: "None",
    value: "default",
    desc: `
    Fastest. Spelling correction shouldn't be necessary in most cases.
    `,
  },
  {
    name: "Emil Japanese",
    value: "emil_j",
    desc: `
    Translations are edited to appear more "natural". Slow.
    `,
  },
  {
    name: "Fill Pro",
    value: "fillpro",
    desc: `
    Uses a model to try and improve pronouns in translations. Will ALWAYS
    use target context and can extend beyond 4 sentences.
    `,
  },
  {
    name: "Langsume",
    value: "langsume",
    desc: `
    Uses a model to predict pronouns for
    translations. Will ALWAYS use source context and can extend
    beyond 4 sentences. Only trained on Japanese-to-English data.   
    `,
  },
  {
    name: "Prepend Source",
    value: "prepend_source_noctx",
    desc: `
    Adds the scanned source text next to the translated text. This can be helpful for debugging along an AMG redrawing app.
    `,
  },
  {
    name: "Prepend Source + Context",
    value: "prepend_source",
    desc: `
    Adds the scanned source text and any context next to the translated text. This can be helpful for debugging along an AMG redrawing app.
    `,
  },
  {
    name: "Elevator",
    value: "elevator",
    desc: `
    Refines the translation with an LLM. INCREDIBLY SLOW!
    `,
  },
  {
    name: "Escalator",
    value: "escalator",
    desc: `
    Refines the translation with the elevator LLM. Can only be activated via the OCR box spelling correction key. Ignored otherwise.
    `,
  },
];
