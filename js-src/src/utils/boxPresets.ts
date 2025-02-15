import { BoxOptions } from "../types/BoxOptions";

type BoxPreset = {
  presetName: string;
  description: string;
  options: BoxOptions;
  disabled: (allBoxIds: string[]) => boolean;
};

const genericOptions = {
  fontSize: 16,
  fontColor: "#FFFFFF",
  textAlign: "left",
  bionicReading: false,
  backgroundColor: "#000000",
  fadeAwayTime: 0,
  fadeInOnEnter: false,
  activationKey: "Escape",
  pauseKey: "Escape",
  xOffset: 290,
  yOffset: 582,
  width: 500,
  height: 228,
  autoScan: false,
  listenClipboard: true,
  backgroundOpacity: 0.8,
  strokeSize: 0,
  strokeColor: "#FFFFFF",
  textDetect: false,
  speakerBox: false,
  removeSpeaker: false,
  useStream: true,
  hideKey: "Escape",
  spellingCorrectionKey: "Escape",
  enabled: true,
  autoEnterTime: 0,
  append: false,
  pipeOutput: "Self",
};

export const OPTIONS_PRESETS: BoxPreset[] = [
  {
    presetName: "Basic",
    description:
      "Translates all text copied in the clipboard at all times and displays the output one character at a time.",
    options: {
      ...genericOptions,
    },
    disabled: () => false,
  },
  {
    presetName: "Ender",
    description:
      "Translates all text copied in the clipboard at all times and only displays the full output.",
    options: {
      ...genericOptions,
      useStream: false,
    },
    disabled: () => false,
  },
  {
    presetName: "Scout Sender",
    description:
      "Translates text in the region when 'a' is pressed. Press 'h' to hide it. Press 'k' to pause it. The text is sent to the 'Scout Receiver' box.",
    options: {
      ...genericOptions,
      fontColor: "#000000",
      backgroundColor: "#FFFFFF",
      activationKey: "a",
      hideKey: "h",
      pauseKey: "k",
      listenClipboard: false,
      backgroundOpacity: 0.75,
      useStream: false,
      pipeOutput: "Receiver",
      boxId: "Sender",
    },
    disabled: (allBoxIds) => !allBoxIds.includes("Receiver"),
  },
  {
    presetName: "Scout Receiver",
    description:
      "Receives output from the 'Scout Sender' box. Useful when you want to translate a region but display the output somewhere else.",
    options: {
      ...genericOptions,
      listenClipboard: false,
      useStream: true,
      pipeOutput: "Self",
      boxId: "Receiver",
      append: true,
    },
    disabled: () => false,
  },
];
