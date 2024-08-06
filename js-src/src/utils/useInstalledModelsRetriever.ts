import { useEffect, useState } from "react";
import { getInstalledModels } from "../flaskcomms/getInstalledModels";

export const useInstalledModelsRetriever = () => {
  const [installedModels, setInstalledModels] = useState<string[]>([]);

  useEffect(() => {
    // Retrieve allowed models from the backend API.
    let canceled = false;

    const cb = async () => {
      if (canceled) return;

      const installedMap = await getInstalledModels();
      // Return model names only if they are truthy (installed).
      setInstalledModels(
        Object.entries(installedMap)
          .filter((x) => x[1])
          .map((x) => x[0])
      );
    };

    cb();

    return () => {
      canceled = true;
    };
  }, []);

  return installedModels;
};