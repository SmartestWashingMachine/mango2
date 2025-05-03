const { contextBridge, ipcRenderer } = require('electron')
const { shell } = require('electron')

const initializeListener = (channel, cb) => {
  // To keep backwards compatiblity we just pass "null" as the event.
  // Even disregarding security with the event arg, we can't simply add and remove the CB (refuses to remove later on)
  // I think that a COPY of the CB is passed to Electron from the client rather than the CB itself, which makes that a headache - but Electron passes the CB itself rather than a copy to the client.
  const strippedCb = (e, ...args) => cb(null, ...args);
  ipcRenderer.on(channel, strippedCb);

  return () => {
    ipcRenderer.removeListener(channel, strippedCb);
  };
};

contextBridge.exposeInMainWorld('electronAPI', {
  readClipboard: () => ipcRenderer.invoke('read-clipboard'), // NOTE: Somewhat insecure - we don't want clients arbitrarily reading the clipboard contents.
  createOcrBox: () => ipcRenderer.send('create-ocr-box'),
  retrieveFiles: (retrieveMode) => ipcRenderer.invoke('retrieve-files', retrieveMode),
  saveBase64Files: (files, folderName, fileName, annotations) => ipcRenderer.invoke('process-files', files, folderName, fileName, annotations),
  saveCsvFile: (csvRows, columnNames) => ipcRenderer.invoke('save-csv-file', csvRows, columnNames),
  setBoxValue: (boxId, k, v) => ipcRenderer.invoke('set-box-value', boxId, k, v),
  getStoreData: () => ipcRenderer.invoke('get-store-data'),
  listenStoreDataChange: (cb) => initializeListener('emit-store-data', cb),
  listenOcrHideChange: (cb) => initializeListener('ocr-hidden', cb),
  listenOcrPauseChange: (cb) => initializeListener('ocr-paused', cb),
  newOcrBox: () => ipcRenderer.invoke('new-ocr-box'),
  deleteOcrBox: (boxId) => ipcRenderer.invoke('delete-ocr-box', boxId),
  connectedOcrBox: (boxId, didConnect) => ipcRenderer.invoke('connected-ocr-box', boxId, didConnect),
  addToTextHistory: (targetTextStrings, sourceTextStrings, newId) => ipcRenderer.invoke('add-to-text-history', targetTextStrings, sourceTextStrings, newId),
  retrieveTextHistory: () => ipcRenderer.invoke('retrieve-text-history'),
  clearTextHistory: () => ipcRenderer.invoke('clear-text-history'),
  showFile: (fullPath) => ipcRenderer.invoke('show-file', fullPath),
  openModelsFolder: () => ipcRenderer.invoke('open-models-folder'),
  openFontsFolder: () => ipcRenderer.invoke('open-fonts-folder'),
  closeApp: () => ipcRenderer.invoke('close-app'),
  expandApp: () => ipcRenderer.invoke('expand-app'),
  hideApp: () => ipcRenderer.invoke('hide-app'),
  openAMG: (filePath) => ipcRenderer.invoke('open-amg', filePath),
  setStoreValue: (k, v) => ipcRenderer.invoke('set-store-value', k, v),
  listenTextHistoryUpdate: (cb) => initializeListener('text-history-updated', cb),
  listenOcrUpdate: (beginCb, doneCb) => {
    const beginListener = ipcRenderer.on('ocr-begin', beginCb);
    const doneListener = ipcRenderer.on('ocr-updated', doneCb);

    return beginListener, doneListener;
  },
  removeOcrUpdateListener: (beginCb, doneCb, boxId) => ipcRenderer.removeListener('ocr-updated'),
  newTerm: () => ipcRenderer.invoke('new-term'),
  updateTerm: (termUuid, key, value) => ipcRenderer.invoke('update-term', termUuid, key, value),
  deleteTerm: (termUuid) => ipcRenderer.invoke('delete-term', termUuid),
  saveImage: (folderName, imageBlob) => ipcRenderer.invoke('save-image', folderName, imageBlob),
  retrieveFontFiles: () => ipcRenderer.invoke('retrieve-font-files'),
  resendData: () => ipcRenderer.invoke('resend-data-change'),
  retrieveImageAddData: () => ipcRenderer.invoke('retrieve-image-add-data'),
  getListenerNames: () => {
    const ex = ipcRenderer.eventNames().map(name => ({ listeners: ipcRenderer.rawListeners(name), channel: name }));
    console.log('ex:');
    console.log(JSON.stringify(ex));

    return ex;
  },
  openHelpWindow: () => ipcRenderer.invoke('open-help-window'),
  importTerms: () => ipcRenderer.invoke('import-terms'),
  exportTerms: () => ipcRenderer.invoke('export-terms'),
  resetSettings: () => ipcRenderer.invoke('reset-settings'),
  openLogsFolder: () => ipcRenderer.invoke('open-logs-folder'),
  openCacheFolder: () => ipcRenderer.invoke('open-cache-folder'),
  regenerateBoxManagers: () => ipcRenderer.invoke('regenerate-box-managers'),
  scanOcrBox: (boxId) => ipcRenderer.invoke('scan-ocr-box', boxId),
  bridgeOn: (evName, cb) => initializeListener(`bridge_${evName}`, cb),
});
