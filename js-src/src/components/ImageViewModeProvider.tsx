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
});

type ImageViewModeProviderProps = {
  children: any;
};

const ImageViewModeProvider = ({ children }: ImageViewModeProviderProps) => {
  const [viewingMode, setViewingMode] = useState<ViewingModes>("one");
  const pushAlert = useAlerts();

  // A little safety hatch!
  useEffect(() => {
    const cb = async (e: KeyboardEvent) => {
      if (e.shiftKey) {
        setViewingMode((v) => (v === "one" ? "vertical" : "one"));

        pushAlert("Changed viewing mode!");
      }
    };

    document.addEventListener("keydown", cb);

    return () => {
      document.removeEventListener("keydown", cb);
    };
  }, []);

  return (
    <ImageViewModeContext.Provider value={{ viewingMode }}>
      {children}
    </ImageViewModeContext.Provider>
  );
};

export const useImageViewMode = () => {
  const pushImageViewMode = useContext(ImageViewModeContext);

  return pushImageViewMode;
};

export default ImageViewModeProvider;
