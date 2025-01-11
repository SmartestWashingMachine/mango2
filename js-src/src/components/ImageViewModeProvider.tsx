import React, {
  useState,
  createContext,
  useContext,
  useCallback,
  useEffect,
} from "react";
import { useAlerts } from "./AlertProvider";

export type ViewingModes = "one" | "vertical";

const ImageViewModeContext = createContext({
  viewingMode: "one" as ViewingModes,
  changeViewingMode: () => {},
});

type ImageViewModeProviderProps = {
  children: any;
};

const ImageViewModeProvider = ({ children }: ImageViewModeProviderProps) => {
  const [viewingMode, setViewingMode] = useState<ViewingModes>("one");
  const pushAlert = useAlerts();

  const changeViewingMode = useCallback(() => {
    setViewingMode((v) => (v === "one" ? "vertical" : "one"));

    pushAlert("Changed viewing mode!");
  }, [pushAlert]);

  return (
    <ImageViewModeContext.Provider value={{ viewingMode, changeViewingMode }}>
      {children}
    </ImageViewModeContext.Provider>
  );
};

export const useImageViewMode = () => {
  const pushImageViewMode = useContext(ImageViewModeContext);

  return pushImageViewMode;
};

export default ImageViewModeProvider;
