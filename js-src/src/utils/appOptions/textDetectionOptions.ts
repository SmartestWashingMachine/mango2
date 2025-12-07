export const TEXT_DETECTION_OPTIONS = [
  {
    name: "D-FINE Large Denoise",
    value: "dfine_l_denoise",
    desc: `
    Laser-focused on detecting speech bubbles.
    `,
  },
  {
    name: "D-FINE Large Group",
    value: "dfine_l_group",
    desc: `
    Will group together nearby speech bubbles, but is less accurate.
    `,
  },
  {
    name: "Union D-FINE Large Denoise",
    value: "union_dfine_denoise",
    desc: `
    Slow but usually gives the best results by merging results from D-FINE Denoise and D-FINE Line EXO-Massive.
    `,
  },
  {
    name: "None",
    value: "none",
    desc: `
    The entire image is used as-is. This is probably only
    desirable if using a text line recognition model or using the detached text box window.
    `,
  },
];
