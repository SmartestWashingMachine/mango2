import { createContext, useContext } from "react";

// loading should be true whenever the backend is processing something (e.g: image translation, text translation, book translation, etc...)
const LoaderContext = createContext({
  loading: false,
  setLoading: (s: boolean) => {},
});

export default LoaderContext;

export const useLoader = () => {
  const contextData = useContext(LoaderContext);

  return contextData;
};
