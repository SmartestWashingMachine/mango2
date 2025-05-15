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
    options: [
      { ...getOpts("Scanner"), boxId: "PRESS > 1", activationKey: "1" },
    ],
  },
  {
    title: "2 boxes",
    description:
      '"I want a box that reads text from the clipboard, and another box that reads text on the screen when I press a button."',
    options: [
      { ...getOpts("Basic"), boxId: "CLIPBOARD" },
      { ...getOpts("Scanner"), boxId: "PRESS > 1", activationKey: "1" },
    ],
  },
  {
    title: "2 boxes",
    description:
      '"I want a box that reads text on the screen when I press a button, and sends the result to another box wherever I place it."',
    options: [
      { ...getOpts("Scout Receiver"), boxId: "READER" },
      {
        ...getOpts("Scout Sender"),
        boxId: "PRESS > 1",
        pipeOutput: "READER",
        activationKey: "1",
      },
    ],
  },
  {
    title: "2 boxes (1 system UI)",
    description:
      '"I want a box that reads text from the clipboard, and another box that reads text on the screen when I press a button, and this box should translate each line individually."',
    options: [
      { ...getOpts("Basic"), boxId: "CLIPBOARD" },
      {
        ...getOpts("Scanner"),
        boxId: "PRESS > 1",
        translateLinesIndividually: 99,
        backgroundColor: "#000000",
        fontColor: "#FFFFFF",
        activationKey: "1",
      },
    ],
  },
  {
    title: "3 boxes",
    description:
      '"I want two boxes that each reads text on the screen with their own buttons, and sends the results to a third box wherever I place it."',
    options: [
      { ...getOpts("Scout Receiver"), boxId: "READER" },
      {
        ...getOpts("Scout Sender"),
        boxId: "PRESS > 1",
        pipeOutput: "READER",
        activationKey: "1",
      },
      {
        ...getOpts("Scanner"),
        boxId: "PRESS > 2",
        pipeOutput: "READER",
        activationKey: "2",
      },
    ],
  },
  {
    title: "3 boxes (1 transparent)",
    description:
      '"I want two boxes that each reads text on the screen with their own buttons, and sends the results to a third box (with a transparent background) wherever I place it."',
    options: [
      { ...getOpts("Scout Receiver Transparent"), boxId: "READER" },
      {
        ...getOpts("Scout Sender"),
        boxId: "PRESS > 1",
        pipeOutput: "READER",
        activationKey: "1",
      },
      {
        ...getOpts("Scanner"),
        boxId: "PRESS > 2",
        pipeOutput: "READER",
        activationKey: "2",
      },
    ],
  },
  {
    title: "3 boxes (1 transparent) (1 system UI)",
    description:
      '"I want two boxes that each reads text on the screen with their own buttons, and sends the results to a third box (with a transparent background) wherever I place it. The second box should translate each line individually."',
    options: [
      { ...getOpts("Scout Receiver Transparent"), boxId: "READER" },
      {
        ...getOpts("Scout Sender"),
        boxId: "PRESS > 1",
        pipeOutput: "READER",
        activationKey: "1",
      },
      {
        ...getOpts("Scanner"),
        boxId: "PRESS > 2",
        pipeOutput: "READER",
        translateLinesIndividually: 99,
        backgroundColor: "#000000",
        fontColor: "#FFFFFF",
        activationKey: "2",
      },
    ],
  },
  {
    title: "4 boxes",
    description:
      '"I want three boxes that each reads text on the screen with their own buttons, and sends the results to a fourth box wherever I place it."',
    options: [
      { ...getOpts("Scout Receiver"), boxId: "READER" },
      {
        ...getOpts("Scout Sender"),
        boxId: "PRESS > 1",
        pipeOutput: "READER",
        activationKey: "1",
      },
      {
        ...getOpts("Scanner"),
        boxId: "PRESS > 2",
        pipeOutput: "READER",
        activationKey: "2",
      },
      {
        ...getOpts("Scanner"),
        boxId: "PRESS > 3",
        pipeOutput: "READER",
        activationKey: "3",
      },
    ],
  },
  {
    title: "4 boxes (1 transparent)",
    description:
      '"I want three boxes that each reads text on the screen with their own buttons, and sends the results to a fourth box (with a transparent background) wherever I place it."',
    options: [
      { ...getOpts("Scout Receiver Transparent"), boxId: "READER" },
      {
        ...getOpts("Scout Sender"),
        boxId: "PRESS > 1",
        pipeOutput: "READER",
        activationKey: "1",
      },
      {
        ...getOpts("Scanner"),
        boxId: "PRESS > 2",
        pipeOutput: "READER",
        activationKey: "2",
      },
      {
        ...getOpts("Scanner"),
        boxId: "PRESS > 3",
        pipeOutput: "READER",
        activationKey: "3",
      },
    ],
  },
  {
    title: "5 boxes (1 transparent)",
    description:
      '"I want four boxes that each reads text on the screen with their own buttons, and sends the results to a fifth box (with a transparent background) wherever I place it."',
    options: [
      { ...getOpts("Scout Receiver Transparent"), boxId: "READER" },
      {
        ...getOpts("Scanner"),
        pipeOutput: "READER",
        activationKey: "1",
        boxId: "PRESS > 1",
      },
      {
        ...getOpts("Scanner"),
        pipeOutput: "READER",
        activationKey: "2",
        boxId: "PRESS > 2",
      },
      {
        ...getOpts("Scanner"),
        pipeOutput: "READER",
        activationKey: "3",
        boxId: "PRESS > 3",
      },
      {
        ...getOpts("Scanner"),
        pipeOutput: "READER",
        activationKey: "4",
        boxId: "PRESS > 4",
      },
    ],
  },
  {
    title: "6 boxes (1 transparent)",
    description:
      '"I want five boxes that each reads text on the screen with their own buttons, and sends the results to a sixth box (with a transparent background) wherever I place it."',
    options: [
      { ...getOpts("Scout Receiver Transparent"), boxId: "READER" },
      {
        ...getOpts("Scanner"),
        pipeOutput: "READER",
        activationKey: "1",
        boxId: "PRESS > 1",
      },
      {
        ...getOpts("Scanner"),
        pipeOutput: "READER",
        activationKey: "2",
        boxId: "PRESS > 2",
      },
      {
        ...getOpts("Scanner"),
        pipeOutput: "READER",
        activationKey: "3",
        boxId: "PRESS > 3",
      },
      {
        ...getOpts("Scanner"),
        pipeOutput: "READER",
        activationKey: "4",
        boxId: "PRESS > 4",
      },
      {
        ...getOpts("Scanner"),
        pipeOutput: "READER",
        activationKey: "5",
        boxId: "PRESS > 5",
      },
    ],
  },
  {
    title: "7 boxes (2 transparent)",
    description:
      '"I want five boxes that each reads text on the screen with their own buttons. 4 boxes send the results to the first transparent box, and 1 box sends the results to the second transparent box."',
    options: [
      { ...getOpts("Scout Receiver Transparent"), boxId: "READER 1" },
      { ...getOpts("Scout Receiver Transparent"), boxId: "READER 2" },
      {
        ...getOpts("Scanner"),
        pipeOutput: "READER 1",
        activationKey: "1",
        boxId: "(R1) > 1",
      },
      {
        ...getOpts("Scanner"),
        pipeOutput: "READER 1",
        activationKey: "2",
        boxId: "(R1) > 2",
      },
      {
        ...getOpts("Scanner"),
        pipeOutput: "READER 1",
        activationKey: "3",
        boxId: "(R1) > 3",
      },
      {
        ...getOpts("Scanner"),
        pipeOutput: "READER 1",
        activationKey: "4",
        boxId: "(R1) > 4",
      },
      {
        ...getOpts("Scanner"),
        pipeOutput: "READER 2",
        activationKey: "5",
        boxId: "(R2) > 5",
      },
    ],
  },
];

// Slightly offset every box so they don't overlap.
for (const useCase of BOX_USE_CASES) {
  for (let i = 0; i < useCase.options.length; i++) {
    useCase.options[i].yOffset -= i * 78;
  }
}

export default BOX_USE_CASES;
