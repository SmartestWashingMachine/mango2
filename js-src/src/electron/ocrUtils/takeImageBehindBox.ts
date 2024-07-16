import { BrowserWindow, screen } from "electron";
import sharp from "sharp";
import screenshot from "screenshot-desktop";

export const takeImageBehindBox = async (ocrWindow: BrowserWindow) => {
  // getBounds() is a bit larger than the actual window size. getContentBounds() seems to be correct.
  let { width, height, x, y } = ocrWindow.getContentBounds();
  const factor = screen.getPrimaryDisplay().scaleFactor;

  const imgBuffer = await screenshot({ format: "png" });

  width = Math.floor(width * factor);
  height = Math.floor(height * factor);
  x = Math.floor(x * factor);
  y = Math.floor(y * factor);

  const finalImgBuffer = await sharp(imgBuffer)
    .extract({ width, height, left: x, top: y })
    .toBuffer();

  return { finalImgBuffer };
};
