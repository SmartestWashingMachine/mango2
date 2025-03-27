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
  fasterScan: false,
  scanAfterEnter: 0,
  serverSideActivationKey: false,
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
    presetName: "Scanner",
    description:
      "Translates text in the region when 'k' is pressed. Press 'h' to hide and pause it.",
    options: {
      ...genericOptions,
      fontColor: "#000000",
      backgroundColor: "#FFFFFF",
      activationKey: "k",
      hideKey: "h",
      pauseKey: "h",
      listenClipboard: false,
      backgroundOpacity: 0.75,
      useStream: true,
      pipeOutput: "Self",
    },
    disabled: () => false,
  },
  {
    presetName: "Scout Sender",
    description:
      "Translates text in the region when 'a' is pressed. Press 'h' to hide and pause it. The text is sent to the 'Scout Receiver' box.",
    options: {
      ...genericOptions,
      fontColor: "#000000",
      backgroundColor: "#FFFFFF",
      activationKey: "a",
      hideKey: "h",
      pauseKey: "h",
      listenClipboard: false,
      backgroundOpacity: 0.75,
      useStream: true,
      pipeOutput: "Receiver",
      boxId: "Sender",
      fasterScan: true,
    },
    disabled: (allBoxIds) => !allBoxIds.includes("Receiver"),
  },
  {
    presetName: "Scout Receiver",
    description:
      "Receives output from the 'Scout Sender' box. Useful when you want to translate a region but display the output somewhere else. Hide by pressing \"q\".",
    options: {
      ...genericOptions,
      listenClipboard: false,
      useStream: true,
      pipeOutput: "Self",
      boxId: "Receiver",
      hideKey: "q",
      append: true,
      fasterScan: true,
    },
    disabled: () => false,
  },
  {
    presetName: "Scout Receiver Transparent",
    description:
      "Functions like the Scout Receiver box but has a transparent background and more visible text.",
    options: {
      ...genericOptions,
      listenClipboard: false,
      useStream: true,
      pipeOutput: "Self",
      boxId: "Receiver",
      append: true,
      fasterScan: true,
      fontSize: 20,
      strokeSize: 3,
      backgroundOpacity: 0.0,
      strokeColor: "#000000",
      fontColor: "#FFFFFF",
    },
    disabled: () => false,
  },
];
