import { makeSocket } from "./makeSocket";

export const translateImages = async (
  files: any,
  tgtContextMemory: string | null,
  taskId: string,
  processFilesByModifiedDate: boolean
) => {
  const apiUrl = "http://localhost:5000/processtask1";

  const formData = new FormData() as any;

  // By default, files seem to be sorted in some... less than natural order.
  // This code snippet attempts to natural sort it. See: https://fuzzytolerance.info/blog/2019/07/19/The-better-way-to-do-natural-sort-in-JavaScript/
  // Note: This isn't a perfect solution - still messes up on some file names.
  /*
  const sortedFiles: any[] = Array.from(files);
  sortedFiles.sort((a: any, b: any) =>
    a.name.localeCompare(b, undefined, { numeric: true, sensitivity: "base" })
  );
  */
  // Screw all that. Simpler approach:
  const sortedFiles: any[] = Array.from(files);

  for (const f of sortedFiles) {
    // We only append image files.
    const allowedExts = ["image/jpeg", "image/png", "image/webp", "image/avif"];
    if (allowedExts.indexOf(f.type) > -1) formData.append("file", f);
  }

  if (tgtContextMemory !== null) {
    formData.append("tgt_context_memory", tgtContextMemory);
  }

  formData.append(
    "nat_sort",
    processFilesByModifiedDate ? "disabled" : "enabled"
  );

  formData.append("task_id", taskId);

  // We don't actually await here. We don't care about the output as the data is transmitted via websockets.
  const output = fetch(apiUrl, {
    method: "POST",
    body: formData,
    headers: {
      Accept: "application/json",
    },
  });

  return sortedFiles.map((f: any, idx: number) => `File ${idx + 1}`) || [];
};

export const pollTranslateImagesStatus = (
  progressCb: (progress: number) => void,
  itemCb: (
    image: string,
    imageName: string,
    annotations?: any,
    remainingImages?: number,
    isFirst?: boolean
  ) => void,
  doneCb: () => void,
  taskId: string
) =>
  new Promise<void>((resolve) => {
    const socket = makeSocket();

    socket.on("connect", () => {
      resolve();
    });

    socket.on("progress_task1", (progress: number) => {
      progressCb(progress || 0);
    });

    socket.on("item_task1", (data) => {
      if (data && data.image && data.imageName && data.taskId === taskId) {
        itemCb(
          data.image,
          data.imageName,
          data.annotations,
          data.remainingImages
        );
      }
    });

    socket.on("done_translating_task1", (data) => {
      if (data && data.taskId !== taskId) return;

      doneCb();
      socket.disconnect();
    });
  });

export const switchCleaningApp = async (mode: string) => {
  const apiUrl = "http://localhost:5000/changecleaning";

  const output = await fetch(apiUrl, {
    method: "POST",
    body: JSON.stringify({ mode }),
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
  });
  if (output.status !== 200) throw Error("Invalid status code.");
};

export const switchRedrawingApp = async (mode: string) => {
  const apiUrl = "http://localhost:5000/changeredrawing";

  const output = await fetch(apiUrl, {
    method: "POST",
    body: JSON.stringify({ mode }),
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
  });
  if (output.status !== 200) throw Error("Invalid status code.");
};

export const switchTileSize = async (tileWidth: number, tileHeight: number) => {
  const apiUrl = "http://localhost:5000/changetilesize";

  const output = await fetch(apiUrl, {
    method: "POST",
    body: JSON.stringify({ tileWidth, tileHeight }),
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
  });
  if (output.status !== 200) throw Error("Invalid status code.");
};
