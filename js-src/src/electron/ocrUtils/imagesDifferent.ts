import looksSame from "looks-same";
import { promisify } from "util";

const asyncLooksSame = promisify(looksSame);

/** Returns True if both images are different. */
export const imagesDifferent = async (image1: Buffer, image2: Buffer) => {
  const result = await asyncLooksSame(image1, image2);
  return !result.equal;
};
