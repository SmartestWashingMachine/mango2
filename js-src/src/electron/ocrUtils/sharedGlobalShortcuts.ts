import { globalShortcut } from "electron";
import { v4 as uuidv4 } from "uuid";

type Fn = () => {};

type ShortcutMap = {
  [key: Electron.Accelerator]: { fn: Fn; fnId: string; }[];
};

const sharedGlobalCut = () => {
  const keyMap: ShortcutMap = {};

  const register = (key: Electron.Accelerator, cb: Fn) => {
    // Add the callback to the list.
    const item = { fn: cb, fnId: uuidv4(), };

    if (!(key in keyMap)) {
      keyMap[key] = [];
    }
    keyMap[key].push(item);

    console.log(`Adding callback for ${key}. There are now ${keyMap[key].length} items.`);

    // .register() silently fails if already taken on that key, so we can safely keep calling it.
    // Invoke every callback in the relevant list.
    globalShortcut.register(key, () => {
      if (key in keyMap) {
        console.log(`Activating callbacks for ${key}. There are ${keyMap[key].length} items.`);

        for (const registeredItem of keyMap[key]) {
          registeredItem.fn();
        }
      } else {
        console.log(`No callbacks for ${key} but tried to activate. (This should never happen!)`);
      }
    });

    return item.fnId;
  };

  const unregister = (key: Electron.Accelerator, cbId: string) => {
    if (!(key in keyMap) || keyMap[key].length === 0) {
      console.log(`Ignoring unregister call - no items in ${key}. (This should never happen!)`);
      return;
    }

    const oldLength = keyMap[key].length;

    keyMap[key] = keyMap[key].filter(x => x.fnId !== cbId);

    if (keyMap[key].length === 0) {
      console.log(`Unregistering Electron shortcut for key ${key} as there are no more items.`);
      globalShortcut.unregister(key);
    }
    else {
      if (oldLength === keyMap[key].length) {
        console.log(`No callback was removed for ${key}. ID: ${cbId} (This should never happen!)`);
      }
      else console.log(`Removed callback for ${key} but keeping Electron shortcut as there are still ${keyMap[key].length} items.`);
    }
  };

  return {
    register,
    unregister,
  };
};

const SharedGlobalCut = sharedGlobalCut();

export default SharedGlobalCut;