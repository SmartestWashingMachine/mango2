import ElectronCommands from "../../types/ElectronCommands";
import { v4 as uuidv4 } from "uuid";
import { GatewayAction } from "../../types/GatewayAction";

const prettifyTokens = (tokens: string[]) =>
  tokens.map((t) =>
    t
      .replace("▁", " ")
      .replace("<pad>", "<start> ")
      .replace("</s>", " <end>")
      .replace("<SEP", " <SEP")
  );

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

      state.texts.push(text);
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
