export const TEXT_DETECTION_OPTIONS = [
  {
    name: "YOLO-TD",
    value: "yolo_td",
    desc: `
    Faster and usually outperforms DETR-G. Recommended for basic
    usage.
    `,
  },
  {
    name: "YOLO-XL",
    value: "yolo_xl",
    desc: `
    Best performing variant. Slower than YOLO-TD.
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
