import { createContext, useContext, useEffect } from "react";
import { triggerCircuitBreak } from "../flaskcomms/optionsViewComms";

// loading should be true whenever the backend is processing something (e.g: image translation, text translation, book translation, etc...)
const LoaderContext = createContext({
  loading: false,
  setLoading: (s: boolean) => { },
});

export default LoaderContext;

export const useLoader = () => {
  const contextData = useContext(LoaderContext);

  // A little safety hatch!
  useEffect(() => {
    const cb = async (e: KeyboardEvent) => {
      if (e.ctrlKey && e.shiftKey && e.key === 'Q') {
        triggerCircuitBreak();
      }
    };

    document.addEventListener('keydown', cb);

    return () => {
      document.removeEventListener('keydown', cb);
    };
  }, []);

  return contextData;
};
