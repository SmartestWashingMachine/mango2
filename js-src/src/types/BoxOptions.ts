export type BoxOptionsFrontend = {
  textAlign: string;
  fontColor: string;
  fontSize: string | number;
  bionicReading: boolean;
  bold: boolean;
  backgroundColor: string;
  fadeAwayTime: number;
  fadeInOnEnter: boolean; // Unused?
  backgroundOpacity: number;
  strokeSize: number;
  strokeColor: string;
  removeSpeaker: boolean; // Removes speaker in string format: <SPEAKER>: <TEXT>
  hideKey: string;
  clickThroughKey: string;
  enabled: boolean;
  autoEnterTime: number;
  append: boolean;
  pipeOutput: string;
  useStream: boolean;
};

export type BoxOptionsBackend = {
  activationKey: string;
  autoScan: boolean;
  listenClipboard: boolean;
  textDetect: boolean;
  pauseKey: string;
  xOffset: number;
  yOffset: number;
  width: number;
  height: number;
  speakerBox: boolean;
  useStream: boolean;
  spellingCorrectionKey: string;
  boxId?: string;
  fasterScan: boolean;
  scanAfterEnter: number;
  serverSideActivationKey: boolean;
  translateLinesIndividually: number;
};

export type BoxOptions = BoxOptionsFrontend & BoxOptionsBackend;
