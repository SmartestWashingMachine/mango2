import ElectronCommands from "../../types/ElectronCommands";
import { v4 as uuidv4 } from "uuid";
import { GatewayAction } from "../../types/GatewayAction";
import { OcrBoxManager } from "../ocrUtils/ocrBox";
import { updateBoxValueInStoreArray } from "../../utils/updateItemInStoreArray";
import { makeBaseBox } from "../ocrUtils/makeBaseBox";

// By create we mean open. To truly make a new OCR box see NEW_OCR_BOX.
const createOcrBox: GatewayAction = {
  command: ElectronCommands.CREATE_OCR_BOX,
  commandType: "on",
  fn: (_, __, state, store) => {
    // TODO: changed in ocrBox to use in setUpBox state.managers.forEach((m) => m.initializeValues());

    const foundSpeakerBox = state.managers.find(
      (x: OcrBoxManager) => x.speakerBox && x.enabled
    ); // Only finds first speaker box, if any exists.

    let speakerCallback;
    const emptySpeakerCallback = () => null;
    if (foundSpeakerBox !== undefined) {
      speakerCallback = () => foundSpeakerBox.scanBoxContents();
    } else {
      speakerCallback = emptySpeakerCallback;
    }

    for (const manager of state.managers) {
      if (manager.ocrWindow !== null) {
        manager.tearDownBox(true, store);
      } else {
        // Obviously the speaker box should not trigger itself!
        const isNotSpeakerItself =
          foundSpeakerBox !== undefined &&
          manager.boxId !== foundSpeakerBox.boxId;
        manager.setUpBox(
          isNotSpeakerItself ? speakerCallback : emptySpeakerCallback
        );
      }
    }
  },
};

const setBoxValue: GatewayAction = {
  command: ElectronCommands.SET_BOX_VALUE,
  commandType: "handle",
  fn: (e, w, s, store, boxId: string, key: string, value: string) => {
    updateBoxValueInStoreArray(store, boxId, key, value);
  },
};

const newOcrBox: GatewayAction = {
  command: ElectronCommands.NEW_OCR_BOX,
  commandType: "handle",
  fn: (e, w, state, store) => {
    const newBoxId = uuidv4();

    // Add box to store.
    const boxes = store.get("boxes") as any[];
    const baseBox = makeBaseBox(newBoxId);
    boxes.push(baseBox);
    store.set("boxes", boxes);

    const newManager = new OcrBoxManager(newBoxId, store, state.texts);
    state.managers.push(newManager);
  },
};

const deleteOcrBox: GatewayAction = {
  command: ElectronCommands.DELETE_OCR_BOX,
  commandType: "handle",
  fn: (e, w, state, store, boxId: string) => {
    const managerToRemove = state.managers.find((m) => m.boxId === boxId);
    if (managerToRemove) managerToRemove.tearDownBox();

    const managersToKeep = state.managers.filter((m) => m.boxId !== boxId);
    state.managers = managersToKeep;

    // Remove box from store.
    const boxes = store.get("boxes") as any[];
    const newBoxes = boxes.filter((b) => b.boxId !== boxId);
    store.set("boxes", newBoxes);

    return;
  },
};

const connectedOcrBox: GatewayAction = {
  command: ElectronCommands.CONNECTED_OCR_BOX,
  commandType: "handle",
  fn: (e, w, state, store, boxId: string, didConnect: boolean) => {
    const found = state.managers.find((m) => m.boxId === boxId);
    if (found) found._websocketLoaded = didConnect;

    return;
  },
};

export default [createOcrBox, setBoxValue, newOcrBox, deleteOcrBox, connectedOcrBox];
