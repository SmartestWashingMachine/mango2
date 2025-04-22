import { BoxOptions } from "../../types/BoxOptions";

export const DEFAULT_BOX_OPTIONS: BoxOptions = {
  fontSize: 16,
  fontColor: "#FFFFFF",
  textAlign: "left",
  bionicReading: false,
  backgroundColor: "#000000",
  fadeAwayTime: 0,
  fadeInOnEnter: false,
  activationKey: "k",
  pauseKey: "q",
  xOffset: 0,
  yOffset: 0,
  width: 600,
  height: 300,
  autoScan: false,
  listenClipboard: false,
  backgroundOpacity: 1,
  strokeSize: 0,
  strokeColor: "#FFFFFF",
  textDetect: false,
  speakerBox: false,
  removeSpeaker: false,
  useStream: false,
  hideKey: "Escape",
  clickThroughKey: "Escape",
  spellingCorrectionKey: "Escape",
  enabled: true,
  autoEnterTime: 0,
  append: false,
  pipeOutput: "Self",
  fasterScan: false,
  scanAfterEnter: 0,
  serverSideActivationKey: false,
  translateLinesIndividually: 0,
};

export const makeBaseBox = (boxId: string) => {
  return {
    ...DEFAULT_BOX_OPTIONS,
    boxId,
  };
};
