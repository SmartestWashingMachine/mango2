export const TEXT_LINE_OPTIONS = [
  {
    name: "None",
    value: "none",
    desc: `
    No model is used to separate a text region into lines. This is usually fine.
    `,
  },
  {
    name: "D-FINE Line EXO-Massive",
    value: "dfine_line_emassive",
    desc: `
    Can scan lines individually and works well with the "None" text detection app for certain games. Nearby lines will be translated as one unit.
    `,
  },
  {
    name: "DETR Line EX-Massive",
    value: "yolo_line_emassive",
    desc: `
    Slightly weaker but slightly faster than D-FINE Line EXO-Massive.
    `,
  },
  {
    name: "(Legacy) DETR Line EX",
    value: "yolo_line_e",
    desc: `
    Can scan lines individually and works well with the "None" text detection app for certain games. Nearby lines will be translated as one unit.
    `,
  },
  {
    name: "(Legacy) YOLO Line Light",
    value: "yolo_line_light",
    desc: `
    Fast and filters out noise. Must be used with a Text Detection model.
    `,
  },
  {
    name: "(Legacy) YOLO Line",
    value: "yolo_line",
    desc: `
    Attempts to detect each text line AFTER detecting speech
    bubbles. Slower.
    `,
  },
  {
    name: "(Legacy) YOLO Line XL",
    value: "yolo_line_xl",
    desc: `
    Stronger but slower than YOLO Line.
    `,
  },
];
