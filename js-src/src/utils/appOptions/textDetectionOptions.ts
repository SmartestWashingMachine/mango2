export const TEXT_DETECTION_OPTIONS = [
  {
    name: "YOLO-TD",
    value: "yolo_td",
    desc: `
    Fast but inaccurate.
    `,
  },
  {
    name: "YOLO-XL",
    value: "yolo_xl",
    desc: `
    Best performing variant. Slower than YOLO-TD. Recommended for general use.
    `,
  },
  {
    name: "Union",
    value: "union",
    desc: `
    Merges results from YOLO-XL and DETR Line EX to give even better results. Slow.
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
