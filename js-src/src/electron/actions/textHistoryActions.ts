import ElectronCommands from "../../types/ElectronCommands";
import { v4 as uuidv4 } from "uuid";
import { GatewayAction } from "../../types/GatewayAction";

const modifyLastNItems = <T>(
  array: T[],
  n: number,
  predicate: (item: T) => boolean,
  modifier: (item: T) => T,
  breakIfModified = true
) => {
  let arrayWasModified = false;

  const startIndex = Math.max(array.length - n, 0);

  // Notice this iterates in reverse-order. Since this is used for updating text history via streamed updates, it's more likely that the item to update is at the bottom or end of the list.
  for (let i = array.length - 1; i >= startIndex; i--) {
    if (predicate(array[i])) {
      arrayWasModified = true;

      array[i] = modifier(array[i]);

      if (breakIfModified) break;
    }
  }

  return arrayWasModified;
};

const retrieveTextHistory: GatewayAction = {
  command: ElectronCommands.RETRIEVE_TEXT_HISTORY,
  commandType: "handle",
  fn: (e, win, state) => {
    return state.texts;
  },
};

const addToTextHistory: GatewayAction = {
  command: ElectronCommands.ADD_TO_TEXT_HISTORY,
  commandType: "handle",
  fn: (e, win, state, store, targetTextStrings, sourceTextStrings, newIds) => {
    if (sourceTextStrings.length !== targetTextStrings.length) {
      throw Error(
        `Source texts amount is not equal to target texts amount. S | T = ${sourceTextStrings.length} | ${targetTextStrings.length}`
      );
    }

    for (let i = 0; i < targetTextStrings.length; i++) {
      const text = {
        sourceText: sourceTextStrings[i],
        targetText: targetTextStrings[i],
        uuid: newIds !== null && newIds !== undefined ? newIds[i] : uuidv4(),
      };

      // Replace instead if the last ID is the same. Used for generic translation tasks (/translate).
      const wasModified = modifyLastNItems(
        state.texts,
        10, // Iterate over last 10 items.
        (
          stateText // Modify that item (stateText) if these conditions are met (same ID & less length).
        ) =>
          stateText.uuid === text.uuid &&
          stateText.targetText[0].length < text.targetText[0].length, // Nested lists. I forgot why.
        () => text // If the predicate (previous parameter) is true, replace that item with our new text.
      );

      if (!wasModified) {
        state.texts.push(text);
      }
    }

    // TODO: Use typing.
    win.webContents.send(ElectronCommands.LISTEN_TEXT_HISTORY, state.texts);
  },
};

const clearTextHistory: GatewayAction = {
  command: ElectronCommands.CLEAR_TEXT_HISTORY,
  commandType: "handle",
  fn: (e, win, state) => {
    state.texts = [];
  },
};

export default [retrieveTextHistory, addToTextHistory, clearTextHistory];
