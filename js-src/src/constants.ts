import path from "path";
import { app } from "electron";

export const APP_LIBRARY_PATH = path.join(
  app.getPath("documents"),
  "./Mango",
  "./images"
);
export const APP_CSV_PATH = path.join(
  app.getPath("documents"),
  "./Mango",
  "./texts"
);
export const APP_LOGS_PATH = path.join(
  app.getPath("documents"),
  "./Mango",
  "./logs"
);
export const APP_FONTS_PATH = path.join(
  path.parse(app.getPath("exe")).dir,
  "resources",
  "fonts"
); // path.join(process.cwd(), "resources/fonts");
export const APP_MODELS_PATH = path.join(
  path.parse(app.getPath("exe")).dir,
  "models"
);

export const APP_CACHE_FOLDER = path.join(
  path.parse(app.getPath("exe")).dir,
  "models",
  "database"
);

export const BACKEND_PATH = path.join(
  path.parse(app.getPath("exe")).dir,
  "resources",
  "backend",
  "run_server.exe"
); // "resources/backend/run_server.exe";

export const DOWNLOADS_PATH = app.getPath("downloads");

export const DISABLED_KEY_VALUE = "Escape"; // In ocrBox and BoxApp.
