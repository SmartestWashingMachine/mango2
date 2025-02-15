import ElectronCommands from "../../types/ElectronCommands";
import IReplaceTerm from "../../types/ReplaceTerm";
import { v4 as uuidv4 } from "uuid";
import { initializeModelNames } from "../../flaskcomms/setFlaskSettings";
import { GatewayAction } from "../../types/GatewayAction";
import { updateTermValueInStoreArray } from "../../utils/updateItemInStoreArray";
import { OPTIONS_PRESETS } from "../../utils/boxPresets";
import { OcrBoxManager } from "../ocrUtils/ocrBox";

const getStoreData: GatewayAction = {
  command: ElectronCommands.GET_STORE_DATA,
  commandType: "handle",
  fn: (_, __, ___, store) => {
    return store.store;
  },
};

const setStoreValue: GatewayAction = {
  command: ElectronCommands.SET_STORE_VALUE,
  commandType: "handle",
  fn: (e, w, s, store, key, value) => {
    store.set(key, value);
  },
};

const resendDataChange: GatewayAction = {
  command: ElectronCommands.RESEND_DATA_CHANGE,
  commandType: "handle",
  fn: async (e, w, s, store) => {
    await initializeModelNames(store.store);
  },
};

const resetSettings: GatewayAction = {
  command: ElectronCommands.RESET_SETTINGS,
  commandType: "handle",
  fn: (e, w, state, store, key, value) => {
    store.clear();

    const boxes = store.get("boxes") as any[];

    if (boxes.length === 0) {
      const boxes = [{ ...OPTIONS_PRESETS[0].options, boxId: "firstbox" }];
      store.set("boxes", boxes);

      state.managers = boxes.map(
        (b) => new OcrBoxManager(b.boxId, store, state.texts)
      );
    }
  },
};

const regenerateBoxManagers: GatewayAction = {
  command: ElectronCommands.REGENERATE_BOX_MANAGERS,
  commandType: "handle",
  fn: (e, w, state, store, key, value) => {
    console.log("regen");
    let boxes = store.get("boxes") as any[];

    if (boxes.length === 0) {
      boxes = [{ ...OPTIONS_PRESETS[0].options, boxId: "firstbox" }];
      store.set("boxes", boxes);
    }

    state.managers = boxes.map(
      (b) => new OcrBoxManager(b.boxId, store, state.texts)
    );
  },
};

// Events for the term array.

const createTerm: GatewayAction = {
  command: ElectronCommands.NEW_TERM,
  commandType: "handle",
  fn: async (e, w, s, store) => {
    const defaultTerm: IReplaceTerm = {
      original: "",
      replacement: "",
      uuid: uuidv4(),
      onSide: "source",
      enabled: true,
    };

    const oldTerms = store.get("terms") as IReplaceTerm[];
    const newTerms = [...oldTerms, defaultTerm] as IReplaceTerm[];
    store.set("terms", newTerms);

    await resendDataChange.fn(e, w, s, store);
  },
};

const deleteTerm: GatewayAction = {
  command: ElectronCommands.DELETE_TERM,
  commandType: "handle",
  fn: async (e, w, s, store, termUuid: string) => {
    const oldTerms = store.get("terms") as IReplaceTerm[];
    const newTerms = oldTerms.filter((x) => x.uuid !== termUuid);
    store.set("terms", newTerms);

    await resendDataChange.fn(e, w, s, store);
  },
};

const updateTerm: GatewayAction = {
  command: ElectronCommands.UPDATE_TERM,
  commandType: "handle",
  fn: (
    e,
    w,
    state,
    store,
    termUuid: string,
    key: keyof IReplaceTerm,
    value: string
  ) => {
    updateTermValueInStoreArray(store, termUuid, key, value);

    const WAIT_TIME = 5000;

    if (state.termUpdateTimer) {
      // Refresh the timer.
      clearTimeout(state.termUpdateTimer);
    }

    state.termUpdateTimer = setTimeout(() => {
      initializeModelNames(store.store);
    }, WAIT_TIME);
  },
};

const retrieveImageModeOptions: GatewayAction = {
  command: ElectronCommands.RETRIEVE_IMAGE_ADD_DATA,
  commandType: "handle",
  fn: (e, w, s, store) => {
    return {
      cleaningMode: store.get("cleaningMode"),
      redrawingMode: store.get("redrawingMode"),
      tileWidth: store.get("tileWidth"),
      tileHeight: store.get("tileHeight"),
    };
  },
};

export default [
  getStoreData,
  setStoreValue,
  resendDataChange,
  regenerateBoxManagers,
  createTerm,
  deleteTerm,
  updateTerm,
  retrieveImageModeOptions,
  resetSettings,
];
