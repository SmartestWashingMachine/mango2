import { BrowserWindow } from "electron";
import { ElectronState } from "../../types/ElectronState";
import {
  refineTranslation,
  scanImageGiveText,
  translateImageGiveText,
} from "../../flaskcomms/ocrBoxBackendComms";
import { imagesDifferent } from "./imagesDifferent";
import { BoxOptionsBackend } from "../../types/BoxOptions";
import { DEFAULT_BOX_OPTIONS } from "./makeBaseBox";
import { StoreAdapter } from "../../types/ElectronStore";
import { updateBoxValueInStoreArray } from "../../utils/updateItemInStoreArray";
import { DISABLED_KEY_VALUE } from "../../constants";
import { createOcrWindow } from "./createOcrWindow";
import { takeImageBehindBox } from "./takeImageBehindBox";
import { clipboardCb, getTextFromClipboard } from "./clipboardCb";
import { autoScanCb } from "./autoScanCb";
import ElectronChannels from "../../types/ElectronChannels";
import SharedGlobalShortcuts from "./sharedGlobalShortcuts";

export class OcrBoxManager implements BoxOptionsBackend {
  ocrWindow: BrowserWindow | null;
  boxId: string;
  activationKey: string;
  width: number;
  height: number;
  xOffset: number;
  yOffset: number;
  autoScan: boolean;
  store?: StoreAdapter;
  prevImage: Buffer | null;
  listenClipboard: boolean;
  prevText: string | null;
  textDetect: boolean;
  pauseKey: string;
  speakerBox: boolean;
  useStream: boolean;
  hideKey: string;
  spellingCorrectionKey: string;
  enabled: boolean;
  pipeOutput: string;

  _timerAutoScan?: any;
  _timerClipboard?: any;
  _paused?: boolean;
  _hide?: boolean;
  _stateTexts: any[];

  _activationKeyCallback: string;
  _pauseKeyCallback: string;
  _hideKeyCallback: string;
  _spellingCorrectionKeyCallback: string;

  _websocketLoaded: boolean;

  _speakerCallback: () => Promise<string>;
  _last_scanned_text: string | null;

  constructor(boxId: string, store: StoreAdapter, stateTexts: any[]) {
    this.ocrWindow = null;
    // boxIds can never be modified. Only created and removed. I guess in theory we could generate duplicate UUIDs, but if that ever happens we might as well just buy a lottery ticket.
    this.boxId = boxId;

    // If store is given, then the box position and sizing will be updated if force closed.
    this.store = store;

    // These settings are overriden later on in createBoxWindow.
    this.width = DEFAULT_BOX_OPTIONS.width;
    this.height = DEFAULT_BOX_OPTIONS.height;
    this.xOffset = DEFAULT_BOX_OPTIONS.xOffset;
    this.yOffset = DEFAULT_BOX_OPTIONS.yOffset;
    this.activationKey = DEFAULT_BOX_OPTIONS.activationKey;
    this.pauseKey = DEFAULT_BOX_OPTIONS.pauseKey;
    this.autoScan = DEFAULT_BOX_OPTIONS.autoScan;
    this.listenClipboard = DEFAULT_BOX_OPTIONS.listenClipboard;
    this.textDetect = DEFAULT_BOX_OPTIONS.textDetect;
    this.speakerBox = DEFAULT_BOX_OPTIONS.speakerBox;
    this.useStream = DEFAULT_BOX_OPTIONS.useStream;
    this.hideKey = DEFAULT_BOX_OPTIONS.hideKey;
    this.spellingCorrectionKey = DEFAULT_BOX_OPTIONS.spellingCorrectionKey;
    this.enabled = DEFAULT_BOX_OPTIONS.enabled;

    this.prevImage = null; // For autoScan.
    this.prevText = null; // For listenClipboard.

    this.pipeOutput = "Self";

    this._timerAutoScan = null;
    this._timerClipboard = null;
    this._paused = false;
    this._hide = false;
    this._speakerCallback = async () => new Promise(() => "");

    this._last_scanned_text = null;
    this._stateTexts = stateTexts;

    this._websocketLoaded = false;

    this._activationKeyCallback = "";
    this._pauseKeyCallback = "";
    this._hideKeyCallback = "";
    this._spellingCorrectionKeyCallback = "";
  }

  getOutputBoxId() {
    // Get the box ID that all updates from the Flask backend should be piped/displayed to.
    if (this.pipeOutput === "Self") return this.boxId;

    return this.pipeOutput;
  }

  // This FN must be called before calling createBoxWindow.
  initializeValues() {
    // Find values for the current box from the store.
    if (!this.store) throw Error("Store must be provided.");

    const boxes = this.store.get("boxes") as any[];

    const boxSettings = boxes.find((b) => b.boxId === this.boxId); // Hooray for in-place updates!

    if (!boxSettings) throw Error("No box found");

    // These settings *should* always be provided... but just in case of shenanigans, there are default values.
    this.activationKey =
      boxSettings.activationKey || DEFAULT_BOX_OPTIONS.activationKey;
    this.pauseKey = boxSettings.pauseKey || DEFAULT_BOX_OPTIONS.pauseKey;
    this.width = boxSettings.width || DEFAULT_BOX_OPTIONS.width;
    this.height = boxSettings.height || DEFAULT_BOX_OPTIONS.height;
    this.xOffset = boxSettings.xOffset || DEFAULT_BOX_OPTIONS.xOffset;
    this.yOffset = boxSettings.yOffset || DEFAULT_BOX_OPTIONS.yOffset;
    this.autoScan = boxSettings.autoScan || DEFAULT_BOX_OPTIONS.autoScan;
    this.listenClipboard =
      boxSettings.listenClipboard || DEFAULT_BOX_OPTIONS.listenClipboard;
    this.textDetect = boxSettings.textDetect || DEFAULT_BOX_OPTIONS.textDetect;
    this.speakerBox = boxSettings.speakerBox || DEFAULT_BOX_OPTIONS.speakerBox;
    this.useStream = boxSettings.useStream || DEFAULT_BOX_OPTIONS.useStream;
    this.hideKey = boxSettings.hideKey || DEFAULT_BOX_OPTIONS.hideKey;
    this.spellingCorrectionKey =
      boxSettings.spellingCorrectionKey ||
      DEFAULT_BOX_OPTIONS.spellingCorrectionKey;
    this.pipeOutput = boxSettings.pipeOutput || DEFAULT_BOX_OPTIONS.pipeOutput;

    if (!boxSettings) {
      this.enabled = true;
    } else this.enabled = boxSettings.enabled;
  }

  createBoxWindow() {
    this.ocrWindow = createOcrWindow({
      width: this.width,
      height: this.height,
      xOffset: this.xOffset,
      yOffset: this.yOffset,
      boxId: this.boxId,
    });
  }

  cloakBox() {
    if (!this.ocrWindow) return;

    // this.ocrWindow.hide();
    //this.ocrWindow.minimize(); - feil
    this.ocrWindow.setOpacity(0); // seems to work. Not the prettiest solution.
    //this.ocrWindow.setSize(0, 0, false); - feil
  }

  revealBox() {
    if (!this.ocrWindow) return;

    this.ocrWindow.setOpacity(1);
  }

  async takeImage() {
    if (!this.ocrWindow) return;

    try {
      return takeImageBehindBox(this.ocrWindow);
    } catch (err) {
      console.log(err);
      return null;
    }
  }

  /* Take an image and return the resulting buffer if not paused and the image is different than the last. */
  async takeImageCheck() {
    this.cloakBox();
    const result = await this.takeImage();
    this.revealBox();

    if (result) {
      if (!this._paused) {
        const isDiff =
          this.prevImage !== null
            ? await imagesDifferent(this.prevImage, result.finalImgBuffer)
            : true;

        if (isDiff) {
          this.prevImage = result.finalImgBuffer;

          return result.finalImgBuffer;
        }
      }
    }
    return null;
  }

  /* Scan and translate. */
  async scanAndTranslateBoxContents() {
    const finalImgBuffer = await this.takeImageCheck();
    if (finalImgBuffer && this._websocketLoaded) {
      await translateImageGiveText(
        [finalImgBuffer],
        this.getOutputBoxId(),
        this.textDetect,
        null,
        this.useStream
      );
    }
  }

  /* Get author/speaker name (untranslated). */
  async scanBoxContents() {
    const finalImgBuffer = await this.takeImageCheck();
    if (!finalImgBuffer) {
      // Image is not different. Proceeding images may have the same author.
      return this._last_scanned_text;
    }

    // This is done wihtout websockets.
    const text: string = await scanImageGiveText(
      [finalImgBuffer],
      this.getOutputBoxId(),
      this.textDetect,
      null
    );

    this._last_scanned_text = text;
    return text;
  }

  setUpBox(speakerCallback: () => Promise<string>) {
    if (this.ocrWindow !== null) return;

    this.initializeValues();

    if (!this.enabled) return;

    this.createBoxWindow();

    // Prepend speaker info if there is a speaker box.
    this._speakerCallback = speakerCallback;

    // Create a listener to detect the required key to scan the box area, and retrieve the result.
    // TODO: No speaker support yet.
    if (this.activationKey !== DISABLED_KEY_VALUE) {
      this._activationKeyCallback = SharedGlobalShortcuts.register(
        this.activationKey,
        async () => {
          await this.scanAndTranslateBoxContents();
        }
      );
    }

    // Toggle pause mode.
    if (this.pauseKey !== DISABLED_KEY_VALUE) {
      this._pauseKeyCallback = SharedGlobalShortcuts.register(
        this.pauseKey,
        async () => {
          this._paused = !this._paused;
          if (this.ocrWindow) {
            this.ocrWindow.webContents.send(
              ElectronChannels.OCR_PAUSED,
              this.boxId,
              this._paused
            );
          }
        }
      );
    }

    // Toggle hide mode.
    if (this.hideKey !== DISABLED_KEY_VALUE) {
      this._hideKeyCallback = SharedGlobalShortcuts.register(
        this.hideKey,
        async () => {
          this._hide = !this._hide;
          if (this.ocrWindow) {
            this.ocrWindow.setIgnoreMouseEvents(this._hide);

            this.ocrWindow.webContents.send(
              ElectronChannels.OCR_HIDDEN,
              this.boxId,
              this._hide
            );
          }
        }
      );
    }

    // Trigger spelling correction refinement for a line of text.
    if (this.spellingCorrectionKey !== DISABLED_KEY_VALUE) {
      this._spellingCorrectionKeyCallback = SharedGlobalShortcuts.register(
        this.spellingCorrectionKey,
        async () => {
          // TODO: Make this work with the OCR mode - not just clipboard.
          if (this.prevText && this._websocketLoaded) {
            //await clipboardCb(this.prevText, opts);

            const newTexts = this._stateTexts;
            if (newTexts.length == 0 || this._paused) return;

            const latest = newTexts[newTexts.length - 1];
            await refineTranslation(
              latest.sourceText,
              latest.targetText,
              this.getOutputBoxId(),
              this.useStream
            );
          }
        }
      );
    }

    if (this.autoScan) {
      /*
        If auto scan is on, then every 3 seconds, take an image and compare it to the previous image taken for this box.
        If the previous image is found to be different than the new image (or the previous does not exist), then send it to the backend.
      */
      const SCAN_MS = 3000;

      const cb = async () => {
        const prevImage = await autoScanCb({
          cloakBox: this.cloakBox,
          revealBox: this.revealBox,
          takeImage: this.takeImage,
          prevImage: this.prevImage,
          boxId: this.getOutputBoxId(),
          useStream: this.useStream,
          textDetect: this.textDetect,
          paused: this._paused,
        });

        if (!!prevImage) this.prevImage = prevImage;
      };

      this._timerAutoScan = setInterval(() => {
        cb();
      }, SCAN_MS);
    }

    if (this.listenClipboard) {
      /*
        If listen clipboard mode is on, then whenever the clipboard content changes, it is sent to the backend-backend as text.
        This mode removes the need for using the OCR model.
      */
      const CHECK_CLIPBOARD_MS = 20;

      const cb = async () => {
        if (!this._websocketLoaded) return;

        const opts = {
          prevText: this.prevText,
          paused: this._paused,
          speakerCallback: this._speakerCallback,
          boxId: this.getOutputBoxId(),
          useStream: this.useStream,
        };

        const result = getTextFromClipboard(opts);
        this.prevText = result[0];
        const isNew = result[1];

        if (isNew && this.prevText) {
          await clipboardCb(this.prevText, opts);
        }
      };

      this._timerClipboard = setInterval(() => {
        cb();
      }, CHECK_CLIPBOARD_MS);
    }

    console.log("Opening OCR BOX:");
    console.log(`X Offset: ${this.xOffset}`);
    console.log(`Y Offset: ${this.yOffset}`);
    console.log(`Width: ${this.width}`);
    console.log(`Height: ${this.height}`);
  }

  tearDownBox(doClose = true, store?: StoreAdapter) {
    if (store && this.ocrWindow) {
      const { width, height, x, y } = this.ocrWindow.getNormalBounds();

      // Update the new positions of the boxes.
      const keys = ["width", "height", "xOffset", "yOffset"];
      const vals = [width, height, x, y];
      for (let i = 0; i < keys.length; i++) {
        updateBoxValueInStoreArray(store, this.boxId, keys[i], vals[i]);
      }
    }

    try {
      if (doClose) this.ocrWindow?.close();
    } catch (err) {
      console.log(err);
    }

    this.ocrWindow = null;
    if (this.activationKey !== DISABLED_KEY_VALUE)
      SharedGlobalShortcuts.unregister(
        this.activationKey,
        this._activationKeyCallback
      );
    if (this.pauseKey !== DISABLED_KEY_VALUE)
      SharedGlobalShortcuts.unregister(this.pauseKey, this._pauseKeyCallback);
    if (this.hideKey !== DISABLED_KEY_VALUE)
      SharedGlobalShortcuts.unregister(this.hideKey, this._hideKeyCallback);
    if (this.spellingCorrectionKey !== DISABLED_KEY_VALUE)
      SharedGlobalShortcuts.unregister(
        this.spellingCorrectionKey,
        this._spellingCorrectionKeyCallback
      );

    if (this._timerAutoScan) clearInterval(this._timerAutoScan);
    if (this._timerClipboard) clearInterval(this._timerClipboard);

    this._paused = false;
    this._hide = false;
  }
}
