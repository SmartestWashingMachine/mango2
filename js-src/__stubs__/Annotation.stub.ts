import IAnnotation from "../src/types/Annotation";

export const createStubAnnotation = (options?: Partial<IAnnotation>) => {
  const stubAnnotation = {
    isBold: false,
    isItalic: false,
    fontFamily: "",
    fontSize: 16,
    fontColor: "red",
    strokeColor: "white",
    strokeSize: 1,
    hasBackgroundColor: false,
    backgroundColor: "black",
    borderRadius: 0,
    textAlign: "center",
    verticalCenter: false,
    text: "",
    x1: 1,
    y1: 1,
    x2: 2,
    y2: 2,
    uuid: "a",
    ...options,
  };

  return stubAnnotation;
};
