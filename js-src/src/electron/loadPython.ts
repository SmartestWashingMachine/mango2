const cp = require("child_process");

import path from "path";
import { BACKEND_PATH } from "../constants";

const getBackendProcess = (backend: string, openShell = false) => {
  if (openShell) {
    return cp.spawn(backend, { shell: true, detached: true, });
  }

  return cp.spawn(backend);
};

export const loadPython = (openShell = false) => {
  // const backend = path.join(process.cwd(), BACKEND_PATH);
  const backend = BACKEND_PATH;

  console.log("Loading backend from path:");
  console.log(backend);

  const subprocess = getBackendProcess(backend, openShell);

  subprocess.stdout.on("data", (data: any) => {
    console.log(data.toString());
  });
  subprocess.stderr.on("data", (data: any) => {
    console.log(data.toString());
  });
  subprocess.on("close", (code: any) => {
    console.log(`Closed backend with code: ${code}`);
  });

  return subprocess;
};

export const closePython = (subprocess: any) => {
  console.log("Closing backend.");

  subprocess.kill();
};
