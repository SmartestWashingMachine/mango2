// So TL;DR: Use nllb_jmad for the fastest translations possible (albeit the slowest to initially load + no context). Use llm_jgem for the highest quality albeit at the cost of speed. Use the other gem models for other languages.
// All the other models are legacy - I don't like them at all.
// It would be soooooo much easier if I could just tune a "massive" LLM (i.e: 14b / 30b / 70b parameters), but this app is intended to be used on low to medium consumer grade hardware.
export const TRANSLATION_OPTIONS = [
  {
    // LET'S GO GAMBLING!!! WOOO I LOVE GOD SEEDS!
    name: "Japanese-2-English Gem",
    value: "llm_jgem",
    desc: `
    Another interesting contender. Somewhat slow.
    `,
  },
  {
    // Seems to be the best performing variant in this app for KO.
    // So it seems quality aware decoding is a bust for KO.
    // One posible remedy would be to instead distil quality data from an LLM (prompt it to predict a scalar score), and train a small regression model from that.
    // But the research papers online discussing the validity of this approach are mixed, and I don't have the funds to create a distilled dataset of satisfactory size.
    name: "Korean-2-English Gem",
    value: "llm_kgem",
    desc: `
    Finetuned for Korean to English. Somewhat slow.
    `,
  },
  {
    name: "Chinese-2-English Gem",
    value: "llm_zhgem",
    desc: `
    Finetuned for Chinese to English. Somewhat slow.
    `,
  },
  {
    // Unlike the normal J-GEM, this one had a second reward model to replicate translations of similar quality to top-performing online systems.
    // Experimented with a few other variants. Here's some of them and why I didn't go further with them:
    // ALMA-7B-R: Old llama model, so tokenization should be inefficient. Also doesn't support context prompting off the bat. It also doesn't work well for more "risque" translations due to its dataset (mainly WMT).
    // Shisa V2 Qwen2.5 7B: Almost always seemed to produce additional headers, thoughts, or translation notes, which meant that I needed to SFT tune it first to align the structure. The baseline translations were also not as good as ALMA-7B-R. However, it could generate more "risque" translations. It seems to be more focused on generating fluent Japanese outputs rather than English outputs. I also don't like Qwen2.5 as a baseline. In addition, context prompting off the bat was flaky.
    name: "Japanese-2-English Goliath",
    value: "llm_jgem_goliath",
    desc: `
    Ridiculously large. Recommended to have at least 12GB of GPU VRAM to run it. Forget about running it on a CPU.
    `,
  },
  {
    name: "Korean-2-English Goliath",
    value: "llm_kgem_goliath",
    desc: `
    Ridiculously large. Recommended to have at least 12GB of GPU VRAM to run it. Forget about running it on a CPU.
    `,
  },
  {
    name: "Chinese-2-English Goliath",
    value: "llm_zhgem_goliath",
    desc: `
    Ridiculously large. Recommended to have at least 12GB of GPU VRAM to run it. Forget about running it on a CPU.
    `,
  },
];

export const LEGACY_TRANSLATION_OPTIONS = [
  {
    // NOTE: nllb_jq is biased towards shorter texts.
    name: "(Legacy) Japanese-2-English Qualia",
    value: "nllb_jq",
    desc: `
    Finetuned for Japanese to English with quality-aware decoding.
    `,
  },
  {
    name: "(Legacy) Japanese-2-English Qualia 300",
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
    // There was another "working" variant that works with context, but I believe the model just "converged" (more like fell) into a local minima - little further learning was going on, and the model's translation quality was more lackluster compared to the non-context one.
    // The non-context one (the current one) was also only trained on a small subset of the dataset (~34%), so it can still be improved.
    name: "(Legacy) Japanese-2-English Madness",
    value: "nllb_jmad",
    desc: `
    The strongest(?) Incredibly slow.
    `,
  },
  {
    name: "(Legacy) Korean-2-English Qualia",
    value: "nllb_ko",
    desc: `
    Finetuned for Korean to English.
    `,
  },
  {
    name: "(Legacy) Chinese-2-English Qualia",
    value: "nllb_zh",
    desc: `
    Finetuned for Chinese to English.
    `,
  },
  {
    name: "(Legacy) Korean-2-English Madness",
    value: "nllb_komad",
    desc: `
    Incredibly slow.
    `,
  },
  {
    name: "(Legacy) Chinese-2-English Madness",
    value: "nllb_zhmad",
    desc: `
    Incredibly slow.
    `,
  },
];
