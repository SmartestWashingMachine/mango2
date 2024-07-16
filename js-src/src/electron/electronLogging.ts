import fs from "fs/promises";
import path from "path";
import log from "electron-log";
import { APP_LOGS_PATH } from "../constants";

log.initialize({ spyRendererConsole: true, preload: false });
log.transports.console.level = "silly";
log.transports.file.level = "silly";
log.errorHandler.startCatching({});

export const makeLogs = async () => {
  await fs.mkdir(APP_LOGS_PATH, { recursive: true });

  const curDate = new Date(Date.now());
  const logName = `ui_logs_${curDate.getDate()}_${
    curDate.getMonth() + 1
  }_${curDate.getFullYear()}.txt`;
  const logPath = path.join(APP_LOGS_PATH, logName);
  log.transports.file.resolvePathFn = () => logPath;

  log.info(`Logging path: ${logPath}`);
};
