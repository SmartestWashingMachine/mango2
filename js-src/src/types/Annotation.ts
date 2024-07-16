export type IAnnotationStyles = {
  isItalic: boolean;
  isBold: boolean;
  fontFamily: string;
  fontSize: number;
  strokeSize: number;
  fontColor: string;
  strokeColor: string;
  hasBackgroundColor: boolean;
  backgroundColor: string;
  borderRadius: number;
  textAlign: string;
  verticalCenter: boolean;
};

type IAnnotation = IAnnotationStyles & {
  text: string;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  uuid: string;
};

export default IAnnotation;
