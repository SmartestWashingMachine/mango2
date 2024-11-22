export const REDRAWING_OPTIONS = [
  {
    name: "Annotate",
    value: "amg_convert",
    desc: `
    The text is only shown when hovered over.
    `,
  },
  {
    name: "Smart",
    value: "smart",
    desc: `
    Draws text while keeping the font size consistent. No word
    breaks. Recommended for basic use.
    `,
  },
  {
    name: "Smart Toons",
    value: "smart_toon",
    desc: `
    Sometimes better than Smart for certain web toons.
    `,
  },
  {
    name: "Smart + BG",
    value: "smart_bg",
    desc: `
    Just like smart but adds an additional white background
    behind the text in case it overlaps the detected region.
    `,
  },
  {
    name: "Global",
    value: "global",
    desc: `
    Draws text while trying to keep the font size consistent.
    `,
  },
  {
    name: "Big Global",
    value: "big_global",
    desc: `
    Just like Global but tries to make the text bigger.
    `,
  },
  {
    name: "Draw & Annotate",
    value: "big_global_amg",
    desc: `
    The text is drawn just like "Big Global" but the image is also
    annotated just in case.
    `,
  },
  {
    name: "Lawless",
    value: "simple",
    desc: `
    Draws text. Each region can have a different font size.
    `,
  },
  {
    name: "Neighbor",
    value: "neighbor",
    desc: `
    Draws the text next to the original text.
    `,
  },
];
