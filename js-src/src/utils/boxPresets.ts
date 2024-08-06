import { BoxOptions } from "../types/BoxOptions";

type BoxPreset = {
  presetName: string;
  description: string;
  options: BoxOptions;
};

export const OPTIONS_PRESETS: BoxPreset[] = [
  {
    presetName: "Basic",
    description:
      "Translates all text copied in the clipboard at all times and displays the output one character at a time.",
    options: {
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
    },
  },
  {
    presetName: "Ender",
    description:
      "Translates all text copied in the clipboard at all times and only displays the full output.",
    options: {
      fontSize: 16,
      fontColor: "#FFFFFF",
      textAlign: "left",
      bionicReading: false,
      backgroundColor: "#000000",
      fadeAwayTime: 0,
      fadeInOnEnter: false,
      activationKey: "Escape",
      pauseKey: "Escape",
      xOffset: 293,
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
      useStream: false,
      hideKey: "Escape",
      spellingCorrectionKey: "Escape",
      enabled: true,
    },
  },
  {
    presetName: "Scanner",
    description:
      "Translates text in the located region whenever 'k' is pressed. Press 'q' to pause it.",
    options: {
      fontSize: 16,
      fontColor: "#000000",
      textAlign: "left",
      bionicReading: false,
      backgroundColor: "#FFFFFF",
      fadeAwayTime: 0,
      fadeInOnEnter: false,
      activationKey: "k",
      pauseKey: "q",
      xOffset: 293,
      yOffset: 582,
      width: 500,
      height: 228,
      autoScan: false,
      listenClipboard: true,
      backgroundOpacity: 0.75,
      strokeSize: 0,
      strokeColor: "#FFFFFF",
      textDetect: false,
      speakerBox: false,
      removeSpeaker: false,
      useStream: false,
      hideKey: "Escape",
      spellingCorrectionKey: "Escape",
      enabled: true,
    },
  },
];
