import { IStoreClientToServer } from "../../types/ElectronStore";

type OptsArr = {
  textDetectionModelName: string[];
  translationModelName: string[];
  textRecognitionModelName: string[];
  textLineModelName: string[];
};

export type PresetItem = {
  name: string;
  description: string;
  opts: Partial<Omit<IStoreClientToServer, keyof OptsArr>> & OptsArr;
};

const GLOBAL_OPTIONS_PARTIAL_PRESETS: PresetItem[] = [
  {
    name: "Manga / Games",
    description:
      "This preset is good for translating Japanese manga panels or for playing games with the detached Text Box.",
    opts: {
      textDetectionModelName: ["dfine_l_denoise", "detr_xl", "yolo_xl"],
      textRecognitionModelName: ["trocr_jmassive", "trocr_jbig"],
      translationModelName: ["llm_jgem", "nllb_jmad", "nllb_jq300", "nllb_jq"],
      textLineModelName: ["none"],
      numBeams: 3,
      bottomTextOnly: false,
      contextAmount: "three",
      tileWidth: 100,
      tileHeight: 100,
      sortTextFromTopLeft: false,
    },
  },
  {
    name: "Manga / Games Alternative",
    description:
      "This preset is also good for translating Japanese manga panels or games. It uses an additional text line detection model to improve the OCR quality.",
    opts: {
      textDetectionModelName: ["dfine_l_denoise", "detr_xl", "yolo_xl"],
      textRecognitionModelName: ["trocr_jmassive", "trocr_jbig"],
      translationModelName: ["llm_jgem", "nllb_jmad", "nllb_jq300", "nllb_jq"],
      textLineModelName: ["dfine_line_emassive", "yolo_line_emassive"],
      numBeams: 3,
      bottomTextOnly: false,
      contextAmount: "three",
      tileWidth: 100,
      tileHeight: 100,
      sortTextFromTopLeft: false,
    },
  },
  {
    name: "Motion Videos",
    description:
      "This preset is good for translating Japanese videos with text drawn on the screen.",
    opts: {
      textDetectionModelName: ["none"],
      textRecognitionModelName: ["trocr_jmagnus"],
      translationModelName: ["llm_jgem", "nllb_jmad", "nllb_jq300", "nllb_jq"],
      textLineModelName: ["dfine_line_emassive", "yolo_line_emassive"],
      numBeams: 3,
      bottomTextOnly: false,
      contextAmount: "three",
      tileWidth: 100,
      tileHeight: 100,
      sortTextFromTopLeft: false,
    },
  },
  {
    name: "Korean Webtoons",
    description: "This preset is good for translating Korean webtoon images.",
    opts: {
      textDetectionModelName: ["dfine_l_denoise", "detr_xl", "yolo_xl"],
      textRecognitionModelName: ["k_trocr_massive"],
      translationModelName: ["llm_kgem", "nllb_komad", "nllb_ko"],
      textLineModelName: ["none"],
      numBeams: 3,
      bottomTextOnly: false,
      contextAmount: "three",
      tileWidth: 100,
      tileHeight: 0,
      sortTextFromTopLeft: true,
    },
  },
];

export default GLOBAL_OPTIONS_PARTIAL_PRESETS;
