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
      "This preset is good for translating Japanese manga panels or games.",
    opts: {
      textDetectionModelName: ["dfine_l_denoise", "detr_xl", "yolo_xl"],
      textRecognitionModelName: ["j_ocr_small", "j_ocr_tiny"],
      translationModelName: ["llm_jgem_goliath", "gem_uni_ja"],
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
      "This preset is good for translating Japanese manga panels or games. It uses an additional text line detection model to improve the OCR quality.",
    opts: {
      textDetectionModelName: ["dfine_l_denoise", "detr_xl", "yolo_xl"],
      textRecognitionModelName: ["j_ocr_small", "j_ocr_small"],
      translationModelName: ["llm_jgem_goliath", "gem_uni_ja"],
      textLineModelName: ["dfine_line_emassive", "none"],
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
      textRecognitionModelName: ["j_ocr_small", "j_ocr_tiny"],
      translationModelName: ["llm_jgem_goliath", "gem_uni_ja"],
      textLineModelName: ["dfine_line_emassive", "none"],
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
      textRecognitionModelName: ["ko_ocr_small", "ko_ocr_tiny"],
      translationModelName: ["llm_kgem_goliath", "gem_uni_ko"],
      textLineModelName: ["dfine_line_emassive", "none"],
      numBeams: 3,
      bottomTextOnly: false,
      contextAmount: "three",
      tileWidth: 100,
      tileHeight: 0,
      sortTextFromTopLeft: true,
    },
  },
  {
    name: "Chinese Comics",
    description: "This preset is good for translating certain Chinese comics.",
    opts: {
      textDetectionModelName: ["dfine_l_denoise", "detr_xl", "yolo_xl"],
      textRecognitionModelName: ["q25_zh", "zh_ocr_tiny"],
      translationModelName: ["llm_zhgem_goliath", "gem_uni_zh"],
      textLineModelName: ["dfine_line_emassive", "none"],
      numBeams: 3,
      bottomTextOnly: false,
      contextAmount: "three",
      tileWidth: 100,
      tileHeight: 100,
      sortTextFromTopLeft: false,
    },
  },
];

export default GLOBAL_OPTIONS_PARTIAL_PRESETS;
