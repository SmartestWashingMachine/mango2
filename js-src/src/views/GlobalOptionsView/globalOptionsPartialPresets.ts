import { IStoreClientToServer } from "../../types/ElectronStore";

export type PresetItem = {
  name: string;
  description: string;
  opts: Partial<IStoreClientToServer>;
}

const GLOBAL_OPTIONS_PARTIAL_PRESETS: PresetItem[] = [
  {
    name: 'Manga / Text Box',
    description: 'This is a basic set of options for translating Japanese manga panels or for use with the text box.',
    opts: {
      textDetectionModelName: 'yolo_xl',
      textRecognitionModelName: 'trocr_jbig',
      translationModelName: 'nllb_jq',
      textLineModelName: 'none',
      numBeams: 3,
      bottomTextOnly: false,
      contextAmount: "zero",
    },
  },
  {
    name: 'Advanced Manga',
    description: 'This is an advanced set of options for translating Japanese manga panels.',
    opts: {
      textDetectionModelName: 'detr_xl',
      textRecognitionModelName: 'trocr_jmassive',
      translationModelName: 'nllb_jq',
      textLineModelName: 'none',
      numBeams: 3,
      bottomTextOnly: false,
      contextAmount: "three",
    },
  },
  {
    name: 'Advanced Manga Alternative',
    description: 'This is an advanced set of options for translating Japanese manga panels.',
    opts: {
      textDetectionModelName: 'detr_xl_xxx',
      textRecognitionModelName: 'trocr_jcomics',
      translationModelName: 'nllb_jq300',
      textLineModelName: 'none',
      numBeams: 3,
      bottomTextOnly: false,
      contextAmount: "three",
    },
  },
  {
    name: 'General Japanese Images',
    description: 'This is an advanced set of options for translating general Japanese images.',
    opts: {
      textDetectionModelName: 'union_massive_detr',
      textRecognitionModelName: 'trocr_jmassive',
      translationModelName: 'nllb_jq',
      textLineModelName: 'none',
      numBeams: 3,
      bottomTextOnly: false,
      contextAmount: "zero",
    },
  },
  {
    name: 'General Japanese Images Alternative',
    description: 'This is an advanced set of options for translating general Japanese images.',
    opts: {
      textDetectionModelName: 'union_massive',
      textRecognitionModelName: 'trocr_jmassive',
      translationModelName: 'nllb_jq',
      textLineModelName: 'none',
      numBeams: 3,
      bottomTextOnly: false,
      contextAmount: "zero",
    },
  },
  {
    name: 'Game Videos / Motion Videos',
    description: 'This is an advanced set of options for translating videos with Japanese texts found near the bottom of the video only.',
    opts: {
      textDetectionModelName: 'none',
      textRecognitionModelName: 'trocr_jmagnus',
      translationModelName: 'nllb_jq',
      textLineModelName: 'yolo_line_emassive',
      numBeams: 3,
      bottomTextOnly: true,
      contextAmount: "zero",
    },
  },
  {
    name: 'General Videos',
    description: 'This is an advanced set of options for translating videos with Japanese texts found anywhere in the video.',
    opts: {
      textDetectionModelName: 'none',
      textRecognitionModelName: 'trocr_jmagnus',
      translationModelName: 'nllb_jq',
      textLineModelName: 'yolo_line_emassive',
      numBeams: 3,
      bottomTextOnly: false,
      contextAmount: "zero",
    },
  },
  {
    name: 'General Korean Images',
    description: 'This is an advanced set of options for translating general Korean images.',
    opts: {
      textDetectionModelName: 'yolo_xl',
      textRecognitionModelName: 'k_trocr_massive',
      translationModelName: 'nllb_ko',
      textLineModelName: 'none',
      numBeams: 3,
      bottomTextOnly: false,
      contextAmount: "zero",
    },
  },
  {
    name: 'General Chinese Images',
    description: 'This is an advanced set of options for translating general Chinese images.',
    opts: {
      textDetectionModelName: 'yolo_xl',
      textRecognitionModelName: 'zh_trocr_massive',
      translationModelName: 'nllb_zh',
      textLineModelName: 'none',
      numBeams: 3,
      bottomTextOnly: false,
      contextAmount: "zero",
    },
  },
];

export default GLOBAL_OPTIONS_PARTIAL_PRESETS;
