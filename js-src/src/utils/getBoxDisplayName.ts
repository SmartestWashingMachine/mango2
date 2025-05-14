import { BoxOptions } from "../types/BoxOptions";

export const getBoxDisplayName = (boxOptions: BoxOptions) => {
  if (!boxOptions) return "";

  let curName = boxOptions.boxId || "";
  if (boxOptions.activationKey !== "Escape") {
    curName = `PRESS > ${boxOptions.activationKey}`;
  } else if (boxOptions.listenClipboard) {
    curName = "CLIPBOARD";
  }

  return `Box (${curName.slice(0, 9)})`;
};
