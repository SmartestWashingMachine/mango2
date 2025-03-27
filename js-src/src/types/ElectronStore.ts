import Store from "electron-store";
import ITextPreset from "./TextPreset";

export type IStoreClientOnly = {
  boxes: any[];
  cacheTargetContext: boolean;
  presets: ITextPreset[];
  cleaningMode: string;
  redrawingMode: string;
  currentView: string;
  currentOcrSubView: string;
  autoOpenOcrWindow: boolean;
};

export type IStoreClientToServer = {
  textLineModelName: string;
  translationModelName: string;
  textDetectionModelName: string;
  textRecognitionModelName: string;
  spellCorrectionModelName: string;
  rerankingModelName: string;
  contextAmount: string;
  enableCuda: boolean;
  maxLengthA: number;
  terms: any[];
  temperature: number;
  topP: number;
  topK: number;
  lengthPenalty: number;
  noRepeatNgramSize: number;
  repetitionPenalty: number;
  epsilonCutoff: number;
  decodingMode: string;
  numBeams: number;
  translationThreads: number;
  forceTranslationCPU: boolean;
  forceTdCpu: boolean;
  forceTlCpu: boolean;
  forceOcrCpu: boolean;
  spellCorrectionSeparate: boolean;
  strokeSize: number;
  bottomTextOnly: boolean;
  tileWidth: number;
  tileHeight: number;
  batchOcr: boolean;
  cutOcrPunct: boolean;
  ignoreDetectSingleWords: boolean;
  sortTextFromTopLeft: boolean;
  useTranslationServer: boolean;
  memoryEfficientTasks: boolean;
};

type IStore = IStoreClientOnly & IStoreClientToServer;

export type StoreAdapter = Store<IStore>;

export default IStore;
