import {
  IStoreClientOnly,
  IStoreClientToServer,
  StoreAdapter,
} from "../types/ElectronStore";

type UpdateItemInStoreArrayOpts = {
  store: StoreAdapter;
  itemId: string;
  idKeyName: string;
  storeKey: keyof IStoreClientToServer | keyof IStoreClientOnly;
  valueName: string;
  value: any;
};

export const updateItemInStoreArray = (opts: UpdateItemInStoreArrayOpts) => {
  const items = opts.store.get(opts.storeKey) as any[];
  for (const itm of items) {
    if (itm[opts.idKeyName] === opts.itemId) {
      itm[opts.valueName] = opts.value;
      break;
    }
  }

  opts.store.set(opts.storeKey, items);
};

export const updateBoxValueInStoreArray = (
  store: StoreAdapter,
  itemId: string,
  key: any,
  value: any
) =>
  updateItemInStoreArray({
    store,
    itemId,
    storeKey: "boxes",
    valueName: key,
    value,
    idKeyName: "boxId",
  });

export const updateTermValueInStoreArray = (
  store: StoreAdapter,
  itemId: string,
  key: any,
  value: any
) =>
  updateItemInStoreArray({
    store,
    itemId,
    storeKey: "terms",
    valueName: key,
    value,
    idKeyName: "uuid",
  });

export const updateNameEntryValueInStoreArray = (
  store: StoreAdapter,
  itemId: string,
  key: any,
  value: any
) =>
  updateItemInStoreArray({
    store,
    itemId,
    storeKey: "nameEntries",
    valueName: key,
    value,
    idKeyName: "uuid",
  });
