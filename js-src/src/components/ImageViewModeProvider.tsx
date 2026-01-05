import React, {
  useState,
  createContext,
  useContext,
  useCallback,
  useEffect,
} from "react";

export type ViewingModes = "one" | "vertical" | "one_amg";

const ImageViewModeContext = createContext({
  viewingMode: "one" as ViewingModes,
  changeViewingMode: (v?: ViewingModes) => {},
  setViewingModeDirectly: (cb: (v: ViewingModes) => ViewingModes) => {},
  viewingAnnotationIdx: 0,
  setViewingAnnotationIdx: (v: number) => {},
  viewingAnnotationTextIdx: 0,
  setViewingAnnotationTextIdx: (v: number) => {},
});

type ImageViewModeProviderProps = {
  children: any;
};

const ImageViewModeProvider = ({ children }: ImageViewModeProviderProps) => {
  const [viewingMode, setViewingMode] = useState<ViewingModes>("one");

  // If one_amg is the current viewing mode. TODO: separate.
  const [viewingAnnotationIdx, setViewingAnnotationIdx] = useState(0); // Annotation bounding box on the left (inside image) is hovered.
  const [viewingAnnotationTextIdx, setViewingAnnotationTextIdx] = useState(0); // Annotation card on the right (outside image) is hovered.

  const changeViewingMode = useCallback((newV?: ViewingModes) => {
    setViewingMode((v) => newV || (v === "one" ? "vertical" : "one"));
  }, []);

  return (
    <ImageViewModeContext.Provider
      value={{
        viewingMode,
        changeViewingMode,
        viewingAnnotationIdx,
        setViewingAnnotationIdx,
        viewingAnnotationTextIdx,
        setViewingAnnotationTextIdx,
        setViewingModeDirectly: setViewingMode,
      }}
    >
      {children}
    </ImageViewModeContext.Provider>
  );
};

export const useImageViewMode = () => {
  const pushImageViewMode = useContext(ImageViewModeContext);

  return pushImageViewMode;
};

export default ImageViewModeProvider;
