// This is like boxPresets, but for whole collections of boxes to satisfy some end task.

import { BoxOptions } from "../types/BoxOptions";
import { OPTIONS_PRESETS } from "./boxPresets";

type BoxUseCase = {
  title: string;
  description: string;
  options: (BoxOptions & { boxId: string })[];
};

const getOpts = (name: string) => {
  const o = OPTIONS_PRESETS.find((o) => o.presetName === name);
  if (!o) {
    throw new Error(`Box preset ${name} not found.`);
  }
  return o.options;
};

const BOX_USE_CASES: BoxUseCase[] = [
  {
    title: "1 box",
    description: '"I want a box that reads text from the clipboard."',
    options: [{ ...getOpts("Basic"), boxId: "CLIPBOARD" }],
  },
  {
    title: "1 transparent box",
    description:
      '"I want a box with a transparent background that reads text from the clipboard."',
    options: [{ ...getOpts("Basic Transparent"), boxId: "CLIPBOARD" }],
  },
  {
    title: "1 box",
    description:
      '"I want a box that reads text on the screen when I press a button."',
    options: [{ ...getOpts("Scanner"), boxId: "PRESS > K" }],
  },
  {
    title: "2 boxes",
    description:
      '"I want a box that reads text from the clipboard, and another box that reads text on the screen when I press a button."',
    options: [
      { ...getOpts("Basic"), boxId: "CLIPBOARD" },
      { ...getOpts("Scanner"), boxId: "PRESS > K" },
    ],
  },
  {
    title: "2 boxes",
    description:
      '"I want a box that reads text on the screen when I press a button, and sends the result to another box wherever I place it."',
    options: [
      { ...getOpts("Scout Receiver"), boxId: "READER" },
      { ...getOpts("Scout Sender"), boxId: "PRESS > A", pipeOutput: "READER" },
    ],
  },
  {
    title: "3 boxes",
    description:
      '"I want two boxes that each reads text on the screen with their own buttons, and sends the results to a third box wherever I place it."',
    options: [
      { ...getOpts("Scout Receiver"), boxId: "READER" },
      { ...getOpts("Scout Sender"), boxId: "PRESS > A", pipeOutput: "READER" },
      { ...getOpts("Scanner"), boxId: "PRESS > K", pipeOutput: "READER" },
    ],
  },
  {
    title: "3 boxes (1 transparent)",
    description:
      '"I want two boxes that each reads text on the screen with their own buttons, and sends the results to a third box (with a transparent background) wherever I place it."',
    options: [
      { ...getOpts("Scout Receiver Transparent"), boxId: "READER" },
      { ...getOpts("Scout Sender"), boxId: "PRESS > A", pipeOutput: "READER" },
      { ...getOpts("Scanner"), boxId: "PRESS > K", pipeOutput: "READER" },
    ],
  },
  {
    title: "4 boxes",
    description:
      '"I want three boxes that each reads text on the screen with their own buttons, and sends the results to a fourth box wherever I place it."',
    options: [
      { ...getOpts("Scout Receiver"), boxId: "READER" },
      { ...getOpts("Scout Sender"), boxId: "PRESS > A", pipeOutput: "READER" },
      { ...getOpts("Scanner"), boxId: "PRESS > K", pipeOutput: "READER" },
      {
        ...getOpts("Scanner"),
        boxId: "PRESS > L",
        pipeOutput: "READER",
        activationKey: "l",
      },
    ],
  },
  {
    title: "4 boxes (1 transparent)",
    description:
      '"I want three boxes that each reads text on the screen with their own buttons, and sends the results to a fourth box (with a transparent background) wherever I place it."',
    options: [
      { ...getOpts("Scout Receiver Transparent"), boxId: "READER" },
      { ...getOpts("Scout Sender"), boxId: "PRESS > A", pipeOutput: "READER" },
      { ...getOpts("Scanner"), boxId: "PRESS > K", pipeOutput: "READER" },
      {
        ...getOpts("Scanner"),
        boxId: "PRESS > L",
        pipeOutput: "READER",
        activationKey: "l",
      },
    ],
  },
];

// Slightly offset every box so they don't overlap.
for (const useCase of BOX_USE_CASES) {
  for (let i = 0; i < useCase.options.length; i++) {
    useCase.options[i].yOffset -= i * 114;
  }
}

export default BOX_USE_CASES;
