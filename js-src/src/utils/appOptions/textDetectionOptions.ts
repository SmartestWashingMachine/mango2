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
    name: "DETR-XL",
    value: "detr_xl",
    desc: `
    Sometimes better than YOLO-XL for smaller speech bubbles.
    `,
  },
  {
    name: "DETR-XL-XXX",
    value: "detr_xl_xxx",
    desc: `
    Sometimes better than DETR-XL.
    `,
  },
  {
    name: "Union YOLO",
    value: "union",
    desc: `
    Merges results from YOLO-XL and DETR Line EX to give even better results. Slow.
    `,
  },
  {
    name: "Union DETR",
    value: "union_detr",
    desc: `
    Merges results from DETR-XL and DETR Line EX to give even better results. Slow.
    `,
  },
  {
    name: "Union YOLO Massive",
    value: "union_massive",
    desc: `
    Merges results from YOLO-XL and DETR Line EX-Massive to give even better results. Very slow.
    `,
  },
  {
    name: "Union DETR Massive",
    value: "union_massive_detr",
    desc: `
    Merges results from YOLO-XL and DETR Line EX-Massive to give even better results. Very slow.
    `,
  },
  {
    name: "Union DETR-XXX Massive",
    value: "union_massive_detr_xxx",
    desc: `
    Merges results from DETR-XL-XXX and DETR Line EX-Massive to give even better results. Very slow.
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
