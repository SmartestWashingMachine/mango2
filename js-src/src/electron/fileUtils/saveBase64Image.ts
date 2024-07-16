import fs from "fs/promises";
import path from "path";
import { APP_LIBRARY_PATH } from "../../constants";
import { v4 as uuidv4 } from "uuid";

export const getI = async (folderPath: string) => {
  // Make the folder if it does not already exist.
  await fs.mkdir(folderPath, { recursive: true });

  // Get all existing file names in folder.
  const fileNames = await fs.readdir(folderPath);

  // Filter for files with integer names (files generated by this app and not renamed by the user).
  const regex = /^[0-9]+\.png$/;
  // Also map the file names to integer values (and slicing off the ".png" portion of the file name).
  const integerValues = fileNames
    .filter((f) => regex.test(f))
    .map((f) => parseInt(f.slice(0, -4), 10));

  let i = integerValues.length > 0 ? Math.max(...integerValues) : 0;
  i += 1;

  return i;
};

/**
 * Write a list of base64 images to the app library folder, or to a folder within the app library if given.
 *
 * If an app folder is given, then each file will have an integer as the name (e.g: 1, 2, 10, 19).
 *  The starting integer is found by retrieving the largest integer file name in that folder, if it exists, and incrementing it by 1.
 *
 * If no app folder is given, then each file will have a random UUID as the name.
 *
 * If annotations is not null and not an empty list, then the image will be saved as an AMG file.
 */
export const saveBase64Images = async (
  base64Images: string[],
  folderName?: string,
  fileName?: string,
  annotations?: any[]
) => {
  const createFile = async (newFullPath: string, b64: string) => {
    if (
      (annotations && annotations.length > 0) ||
      newFullPath.endsWith(".amg")
    ) {
      // Save as AMG file.
      const data = JSON.stringify({
        image: b64,
        annotations,
      });

      await fs.writeFile(newFullPath, data, "utf-8");
    } else {
      // Save as image.
      await fs.writeFile(newFullPath, b64, "base64");
    }
  };

  let folderPath = APP_LIBRARY_PATH;

  try {
    if (!folderName) {
      for (const b64 of base64Images) {
        const newFileName = fileName || `${uuidv4()}.png`;
        let newFullPath = path.join(APP_LIBRARY_PATH, newFileName);

        await createFile(newFullPath, b64);
      }
    } else {
      folderPath = path.join(APP_LIBRARY_PATH, folderName);

      let i = await getI(folderPath);

      for (const b64 of base64Images) {
        const newFileName = fileName || `${i}.png`;

        let newFullPath = path.join(APP_LIBRARY_PATH, folderName, newFileName);
        await createFile(newFullPath, b64);

        i += 1;
      }
    }

    return {
      folderPath,
    };
  } catch (err) {
    console.log(err);

    return {
      folderPath,
    };
  }
};
