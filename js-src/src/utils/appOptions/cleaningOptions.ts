export const CLEANING_OPTIONS = [
  {
    name: "None",
    value: "none",
    desc: `
    Does not attempt to erase the text at all. Probably only
    desirable if redrawing with the "Neighbor" mode.
    `,
  },
  {
    name: "Simple",
    value: "simple",
    desc: `
    Draws a white box over detected text regions. Recommended for basic use.
    `,
  },
  {
    name: "Simple Adaptive",
    value: "adaptive_clean",
    desc: `
    Draws a colored box over detected text regions. The color
    changes depending on the background color.
    `,
  },
  {
    name: "Blur",
    value: "blur",
    desc: `
    Blurs the detected text regions.
    `,
  },
  {
    name: "Telea",
    value: "telea",
    desc: `
    Uses a fancy algorithm to attempt erasing text only.
    `,
  },
  {
    name: "F-Telea",
    value: "smart_telea",
    desc: `
    Uses a fancy algorithm and some AI magic to attempt erasing text
    only.
    `,
  },
  {
    name: "F-Telea/Blur",
    value: "blur_mask",
    desc: `
    Uses a fancy algorithm and some AI magic to attempt erasing text
    and blurring harder regions.
    `,
  },
  {
    name: "Text Clean",
    value: "text_clean",
    desc: `
    Uses AI to only fill areas with detected characters with white
    pixels.
    `,
  },
  {
    name: "F-Net Edge",
    value: "edge_connect",
    desc: `
    Uses AI to try and automagically erase text. Slow.
    `,
  },
  {
    name: "Paintball",
    value: "paintball",
    desc: `
    Uses AI to try and automagically erase text. Very slow.
    `,
  },
];
