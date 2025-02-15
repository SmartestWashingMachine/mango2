import { BoxOptions } from "../types/BoxOptions";

type BoxPreset = {
  presetName: string;
  description: string;
  options: BoxOptions;
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
  backgroundOpacity: 1,
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
};

export const OPTIONS_PRESETS: BoxPreset[] = [
  {
    presetName: "Basic",
    description:
      "Translates all text copied in the clipboard at all times and displays the output one character at a time.",
    options: {
      ...genericOptions,
    },
  },
  {
    presetName: "Ender",
    description:
      "Translates all text copied in the clipboard at all times and only displays the full output.",
    options: {
      ...genericOptions,
      useStream: false,
    },
  },
  {
    presetName: "Scanner",
    description:
      "Translates text in the located region whenever 'k' is pressed. Press 'q' to pause it.",
    options: {
      ...genericOptions,
      fontColor: "#000000",
      backgroundColor: "#FFFFFF",
      activationKey: "k",
      pauseKey: "q",
      listenClipboard: false,
      backgroundOpacity: 0.75,
      useStream: false,
    },
  },
];
