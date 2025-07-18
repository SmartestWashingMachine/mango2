enum ElectronCommands {
  RETRIEVE_FILES = "retrieve-files",
  CREATE_FILE = "create-file",
  CREATE_OCR_BOX = "create-ocr-box",
  PROCESS_FILES = "process-files",
  SAVE_CSV_FILE = "save-csv-file",
  SET_BOX_VALUE = "set-box-value",
  GET_STORE_DATA = "get-store-data",
  NEW_OCR_BOX = "new-ocr-box",
  DELETE_OCR_BOX = "delete-ocr-box",
  RETRIEVE_TEXT_HISTORY = "retrieve-text-history",
  ADD_TO_TEXT_HISTORY = "add-to-text-history",
  CLEAR_TEXT_HISTORY = "clear-text-history",
  CLOSE_APP = "close-app",
  EXPAND_APP = "expand-app",
  HIDE_APP = "hide-app",
  OPEN_AMG = "open-amg",
  SET_STORE_VALUE = "set-store-value",
  LISTEN_TEXT_HISTORY = "text-history-updated",
  NEW_TERM = "new-term",
  UPDATE_TERM = "update-term",
  DELETE_TERM = "delete-term",
  SAVE_IMAGE = "save-image",
  RETRIEVE_FONT_FILES = "retrieve-font-files",
  RESEND_DATA_CHANGE = "resend-data-change",
  RETRIEVE_IMAGE_ADD_DATA = "retrieve-image-add-data",
  OPEN_HELP_WINDOW = "open-help-window",
  SHOW_FILE = "show-file",
  OPEN_MODELS_FOLDER = "open-models-folder",
  OPEN_FONTS_FOLDER = "open-fonts-folder",
  OPEN_LOGS_FOLDER = "open-logs-folder",
  OPEN_CACHE_FOLDER = "open-cache-folder",
  IMPORT_TERMS = "import-terms",
  EXPORT_TERMS = "export-terms",
  RESET_SETTINGS = "reset-settings",
  CONNECTED_OCR_BOX = "connected-ocr-box",
  READ_CLIPBOARD = "read-clipboard",
  REGENERATE_BOX_MANAGERS = "regenerate-box-managers",
  SCAN_OCR_BOX = "scan-ocr-box",
  READ_DANGEROUS_CONFIG = "read-dangerous-config",
  NEW_NAME_ENTRY = "new-name-entry",
  UPDATE_NAME_ENTRY = "update-name-entry",
  DELETE_NAME_ENTRY = "delete-name-entry",
}

export default ElectronCommands;
