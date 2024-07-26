import Store from "electron-store";
import IStore from "../types/ElectronStore";

const storeDefaults: IStore = {
  boxes: [],
  textLineModelName: "none",
  translationModelName: "nllb_jq",
  textDetectionModelName: "yolo_xl",
  textRecognitionModelName: "trocr_jbig",
  spellCorrectionModelName: "default",
  rerankingModelName: "none",
  contextAmount: "three",
  enableCuda: false,
  maxLengthA: 0,
  terms: [],
  cacheTargetContext: false,
  temperature: 1,
  topP: 0,
  topK: 0,
  lengthPenalty: 1,
  noRepeatNgramSize: 5,
  repetitionPenalty: 1.2,
  epsilonCutoff: 0.0,
  decodingMode: "beam",
  presets: [],
  numBeams: 3,
  translationThreads: 2,
  forceTranslationCPU: true,
  forceTdCpu: false,
  cleaningMode: "adaptive_clean",
  redrawingMode: "smart",
  currentView: "Text",
  autoOpenOcrWindow: false,
  spellCorrectionSeparate: false, // TODO: Unused. Probably don't need it either.
  strokeSize: 1.5,
};

export const initializeStore = () => {
  // Persistent data that can be set on the client and affects the backend.
  const store = new Store<IStore>({
    defaults: storeDefaults,
  });

  // Juuust in case.
  for (const key in storeDefaults) {
    if (!store.get(key)) store.set(key, storeDefaults[key as keyof IStore]);
  }

  return store;
};
