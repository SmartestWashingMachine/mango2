export type ElectronState = {
  managers: any[];
  texts: any[]; // object.
  termUpdateTimer?: any; // Referenced in configStoreActions. Update terms in API when some time passes after a change occurs.
};
