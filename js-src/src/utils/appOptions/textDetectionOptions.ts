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
    Decent performing variant. Slower than YOLO-TD.
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
    name: "D-FINE Medium",
    value: "dfine_m",
    desc: `
    Fast and usually better than the DETR and YOLO models.
    `,
  },
  {
    name: "D-FINE Large",
    value: "dfine_l",
    desc: `
    A good all-around pick. Generally better than the DETR and YOLO models.
    `,
  },
  {
    name: "D-FINE Large Denoise",
    value: "dfine_l_denoise",
    desc: `
    Similar to D-FINE Large but laser-focused on detecting speech bubbles. Less false positives.
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
    name: "Union D-FINE Large Noisy",
    value: "union_dfine_noisy",
    desc: `
    Slow but is almost sure to find missing text boxes... and more by merging results from D-FINE & Line EXO-Massive.
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
