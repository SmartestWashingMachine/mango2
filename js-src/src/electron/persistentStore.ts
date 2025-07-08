import Store from "electron-store";
import IStore from "../types/ElectronStore";

const storeDefaults: IStore = {
  boxes: [],
  textLineModelName: "dfine_line_emassive",
  translationModelName: "llm_jgem",
  textDetectionModelName: "dfine_l_denoise",
  textRecognitionModelName: "trocr_jmassive",
  spellCorrectionModelName: "default",
  rerankingModelName: "none",
  contextAmount: "zero",
  enableCuda: false,
  maxLengthA: 0,
  terms: [],
  cacheTargetContext: false, // TODO: remove
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
  numGpuLayersMt: 22,
  translationThreads: 2, // TODO: remove
  forceTranslationCPU: false,
  forceSpellingCorrectionCPU: true,
  forceTdCpu: false,
  forceTlCpu: false,
  forceOcrCpu: false,
  cleaningMode: "blur",
  redrawingMode: "smart",
  currentView: "Image",
  currentOcrSubView: "basic",
  autoOpenOcrWindow: false,
  spellCorrectionSeparate: false, // TODO: Unused. Probably don't need it either.
  strokeSize: 1.0,
  bottomTextOnly: false,
  tileWidth: 100,
  tileHeight: 100,
  batchOcr: false,
  cutOcrPunct: false,
  ignoreDetectSingleWords: false,
  sortTextFromTopLeft: false,
  useTranslationServer: false,
  memoryEfficientTasks: false,
  cacheMt: false,
  captureWindow: "",
  nameEntries: [],
};

export const initializeStore = () => {
  // Persistent data that can be set on the client and affects the backend.
  const store = new Store<IStore>({
    defaults: storeDefaults,
  });

  // Juuust in case.
  for (const key in storeDefaults) {
    const cur = store.get(key);
    if (cur === null || cur === undefined)
      store.set(key, storeDefaults[key as keyof IStore]);
  }

  return store;
};
