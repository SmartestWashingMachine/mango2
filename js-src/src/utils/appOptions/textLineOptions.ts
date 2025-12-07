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
];
