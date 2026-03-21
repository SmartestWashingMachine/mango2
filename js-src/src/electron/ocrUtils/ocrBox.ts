import { BrowserWindow, screen, ipcMain } from "electron";
import { ElectronState } from "../../types/ElectronState";
import {
  refineTranslation,
  scanImageGiveText,
  translateImageGiveText,
  translateImageGiveTextFaster,
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
import {
  triggerEnterNodeFetch,
  rememberBoxActivationData,
  forgetBoxActivationData,
} from "../../flaskcomms/ocrBoxBackendComms";

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
  listenAudio: boolean;
  prevText: string | null;
  textDetect: boolean;
  pauseKey: string;
  speakerBox: boolean;
  useStream: boolean;
  hideKey: string;
  clickThroughKey: string;
  spellingCorrectionKey: string;
  enabled: boolean;
  pipeOutput: string;
  fasterScan: boolean;
  scanAfterEnter: number;
  serverSideActivationKey: boolean;
  translateLinesIndividually: number;
  joinLinesUntilFinds: string;
  detectSpeakerName: boolean;
  followsCursor: boolean;
  contentProtection: boolean;

  followKey: string;
  showText: boolean;
  outlineColor: string;
  outlineSize: number;

  _timerAutoScan?: any;
  _timerClipboard?: any;
  _timerScanAfterEnter?: any;
  _timerFollowsCursor?: any;
  _paused?: boolean;
  _hide?: boolean;
  _follow?: boolean;
  _clickThrough?: boolean;
  _stateTexts: any[];

  _activationKeyCallback: string;
  _pauseKeyCallback: string;
  _hideKeyCallback: string;
  _followKeyCallback: string;
  _clickThroughKeyCallback: string;
  _spellingCorrectionKeyCallback: string;

  _websocketLoaded: boolean;

  _speakerCallback: () => Promise<string>;
  _last_scanned_text: string | null;

  _hideRecordingBoxesCallback: (boxId: string) => void;
  _revealRecordingBoxesCallback: (_: any, boxId: string) => void; // Removed on cleanup as it interacts with ipcMain.

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
    this.listenAudio = DEFAULT_BOX_OPTIONS.listenAudio;
    this.textDetect = DEFAULT_BOX_OPTIONS.textDetect;
    this.speakerBox = DEFAULT_BOX_OPTIONS.speakerBox;
    this.useStream = DEFAULT_BOX_OPTIONS.useStream;
    this.hideKey = DEFAULT_BOX_OPTIONS.hideKey;
    this.clickThroughKey = DEFAULT_BOX_OPTIONS.clickThroughKey;
    this.spellingCorrectionKey = DEFAULT_BOX_OPTIONS.spellingCorrectionKey;
    this.followsCursor = DEFAULT_BOX_OPTIONS.followsCursor;
    this.contentProtection = DEFAULT_BOX_OPTIONS.contentProtection;
    this.enabled = DEFAULT_BOX_OPTIONS.enabled;

    this.translateLinesIndividually =
      DEFAULT_BOX_OPTIONS.translateLinesIndividually;

    this.joinLinesUntilFinds = DEFAULT_BOX_OPTIONS.joinLinesUntilFinds;
    this.detectSpeakerName = DEFAULT_BOX_OPTIONS.detectSpeakerName;

    this.followKey = DEFAULT_BOX_OPTIONS.followKey;
    this.showText = DEFAULT_BOX_OPTIONS.showText;
    this.outlineColor = DEFAULT_BOX_OPTIONS.outlineColor;
    this.outlineSize = DEFAULT_BOX_OPTIONS.outlineSize;

    this.prevImage = null; // For autoScan.
    this.prevText = null; // For listenClipboard.

    this.pipeOutput = "Self";
    this.fasterScan = false;
    this.scanAfterEnter = 0;
    this.serverSideActivationKey = false;

    this._timerAutoScan = null;
    this._timerClipboard = null;
    this._timerScanAfterEnter = null;
    this._timerFollowsCursor = null;
    this._paused = false;
    this._hide = false;
    this._follow = false;
    this._clickThrough = false;
    this._speakerCallback = async () => new Promise(() => "");

    this._hideRecordingBoxesCallback = () => {};
    this._revealRecordingBoxesCallback = () => {};

    this._last_scanned_text = null;
    this._stateTexts = stateTexts;

    this._websocketLoaded = false;

    this._activationKeyCallback = "";
    this._pauseKeyCallback = "";
    this._hideKeyCallback = "";
    this._followKeyCallback = "";
    this._clickThroughKeyCallback = "";
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
    this.listenAudio =
      boxSettings.listenAudio || DEFAULT_BOX_OPTIONS.listenAudio;
    this.textDetect = boxSettings.textDetect || DEFAULT_BOX_OPTIONS.textDetect;
    this.speakerBox = boxSettings.speakerBox || DEFAULT_BOX_OPTIONS.speakerBox;
    this.contentProtection =
      boxSettings.contentProtection !== undefined
        ? boxSettings.contentProtection
        : DEFAULT_BOX_OPTIONS.contentProtection;
    this.useStream = boxSettings.useStream || DEFAULT_BOX_OPTIONS.useStream;
    this.hideKey = boxSettings.hideKey || DEFAULT_BOX_OPTIONS.hideKey;
    this.clickThroughKey =
      boxSettings.clickThroughKey || DEFAULT_BOX_OPTIONS.clickThroughKey;
    this.spellingCorrectionKey =
      boxSettings.spellingCorrectionKey ||
      DEFAULT_BOX_OPTIONS.spellingCorrectionKey;
    this.pipeOutput = boxSettings.pipeOutput || DEFAULT_BOX_OPTIONS.pipeOutput;
    this.fasterScan = boxSettings.fasterScan || DEFAULT_BOX_OPTIONS.fasterScan;
    this.scanAfterEnter =
      boxSettings.scanAfterEnter || DEFAULT_BOX_OPTIONS.scanAfterEnter;
    this.serverSideActivationKey =
      boxSettings.serverSideActivationKey ||
      DEFAULT_BOX_OPTIONS.serverSideActivationKey;

    this.translateLinesIndividually =
      boxSettings.translateLinesIndividually ||
      DEFAULT_BOX_OPTIONS.translateLinesIndividually;

    this.joinLinesUntilFinds =
      boxSettings.joinLinesUntilFinds ||
      DEFAULT_BOX_OPTIONS.joinLinesUntilFinds;

    this.detectSpeakerName =
      boxSettings.detectSpeakerName || DEFAULT_BOX_OPTIONS.detectSpeakerName;

    this.followsCursor =
      boxSettings.followsCursor || DEFAULT_BOX_OPTIONS.followsCursor;

    this.followKey = boxSettings.followKey || DEFAULT_BOX_OPTIONS.followKey;
    this.showText = boxSettings.showText || DEFAULT_BOX_OPTIONS.showText;
    this.outlineColor =
      boxSettings.outlineColor || DEFAULT_BOX_OPTIONS.outlineColor;
    this.outlineSize =
      boxSettings.outlineSize || DEFAULT_BOX_OPTIONS.outlineSize;

    if (!boxSettings) {
      this.enabled = true;
    } else this.enabled = boxSettings.enabled;
  }

  createBoxWindow() {
    return createOcrWindow({
      width: this.width,
      height: this.height,
      xOffset: this.xOffset,
      yOffset: this.yOffset,
      boxId: this.boxId,
      contentProtection: this.contentProtection,
    });
  }

  cloakBox() {
    // no-op on self: Since we use setContentProtection now we don't need to hide the box - Windows will automatically ignor
    // ... instead, we "hide" all the boxes that are configured to be hidden while scanning. This way no box will scan the other.
    this._hideRecordingBoxesCallback(this.boxId);
  }

  revealBox() {
    if (!this.ocrWindow) return;

    this.ocrWindow.setOpacity(1);

    // Instead, a websocket is used - this._revealRecordingBoxesCallback(this.boxId);
    // That way, we can immediately reveal the boxes when the image is grabbed, rather than when the translation is complete.
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
        this.useStream,
        this.translateLinesIndividually,
        this.joinLinesUntilFinds,
        this.detectSpeakerName
      );
    }
  }

  getCoords = () => {
    if (!this.ocrWindow) return [0, 0, 1, 1];

    let { width, height, x, y } = this.ocrWindow.getContentBounds();
    const factor = screen.getPrimaryDisplay().scaleFactor;

    width = Math.floor(width * factor);
    height = Math.floor(height * factor);
    x = Math.floor(x * factor);
    y = Math.floor(y * factor);

    return [x, y, width, height];
  };

  async scanAndTranslateBoxContentsFaster() {
    if (!this.ocrWindow) return;

    const coords = this.getCoords();

    const isHidden = this._hide;
    this.cloakBox();

    await translateImageGiveTextFaster(
      coords,
      this.getOutputBoxId(),
      this.textDetect,
      null,
      this.useStream,
      this.translateLinesIndividually,
      this.joinLinesUntilFinds,
      this.detectSpeakerName
    );

    if (!isHidden) this.revealBox();
  }

  async scanAndTranslateBox() {
    return this.fasterScan
      ? this.scanAndTranslateBoxContentsFaster()
      : this.scanAndTranslateBoxContents();
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

  rememberThisBox() {
    // important TODO: add "joinLinesUntilFinds" and "detectSpeakerName" here too.

    const coords = this.getCoords();
    rememberBoxActivationData({
      x1: coords[0],
      y1: coords[1],
      width: coords[2],
      height: coords[3],
      box_id: this.getOutputBoxId(),
      this_box_id: this.boxId,
      with_text_detect: this.textDetect,
      use_stream: this.useStream,
      activation_key: this.activationKey,
      translate_lines_individually: this.translateLinesIndividually,
    });
  }

  forgetThisBox() {
    forgetBoxActivationData(this.getOutputBoxId(), this.boxId);
  }

  registerBoxListeningAudio() {
    // make POST call with boxId
  }

  unregisterBoxListeningAudio() {
    // make POST call with boxId
  }

  follow() {
    if (!this.ocrWindow) return;

    const sz = this.ocrWindow.getSize();

    // ElectronJS bug requires a fixed size to be used -_-
    let prevWidth = sz[0];
    let prevHeight = sz[1];

    this._timerFollowsCursor = setInterval(() => {
      if (!this.ocrWindow) return;

      try {
        const windowBounds = this.ocrWindow.getContentBounds();
        const windowWidth = windowBounds.width;
        const windowHeight = windowBounds.height;

        const point = screen.getCursorScreenPoint();

        // Center
        const x = point.x - windowWidth / 2;
        const y = point.y - windowHeight / 2;

        this.ocrWindow.setBounds({
          width: prevWidth,
          height: prevHeight,
          x: Math.round(x),
          y: Math.round(y),
        });
      } catch (err) {
        // Sometimes an error happens when moving out of the screen bounds, so we just gotta catch it.
      }
    }, 15);

    // Cleanup function.
    return () => {
      clearInterval(this._timerFollowsCursor);
      this._timerFollowsCursor = null;
    };
  }

  setUpBox(
    speakerCallback: () => Promise<string>,
    hideRecordingBoxesCallback: (boxId: string) => void,
    revealRecordingBoxesCallback: (boxId: string) => void
  ) {
    if (this.ocrWindow !== null) return;

    this.initializeValues();

    if (!this.enabled) return;

    this.ocrWindow = this.createBoxWindow();

    this._hideRecordingBoxesCallback = hideRecordingBoxesCallback;

    // This one is removed on cleanup as it interacts with IPC main.
    this._revealRecordingBoxesCallback = (_: any, boxId: string) => {
      revealRecordingBoxesCallback(boxId);
    };
    ipcMain.on("task3_image_grabbed", this._revealRecordingBoxesCallback);

    // Prepend speaker info if there is a speaker box.
    this._speakerCallback = speakerCallback;

    // Create a listener to detect the required key to scan the box area, and retrieve the result.
    // TODO: No speaker support yet.
    if (
      this.activationKey !== DISABLED_KEY_VALUE &&
      !this.serverSideActivationKey
    ) {
      this._activationKeyCallback = SharedGlobalShortcuts.register(
        this.activationKey,
        async () => this.scanAndTranslateBox()
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

    // Toggle follow mode.
    if (this.followKey !== DISABLED_KEY_VALUE) {
      let cleanupFollow: any = null;

      this._followKeyCallback = SharedGlobalShortcuts.register(
        this.followKey,
        async () => {
          this._follow = !this._follow;
          if (cleanupFollow) {
            cleanupFollow();
            cleanupFollow = null;
          }

          if (this._follow) {
            cleanupFollow = this.follow();
          }
        }
      );
    }

    // Toggle click-through mode.
    if (this.clickThroughKey !== DISABLED_KEY_VALUE) {
      this._clickThroughKeyCallback = SharedGlobalShortcuts.register(
        this.clickThroughKey,
        async () => {
          this._clickThrough = !this._clickThrough;
          if (this.ocrWindow) {
            this.ocrWindow.setIgnoreMouseEvents(this._clickThrough);

            this.ocrWindow.webContents.send(
              ElectronChannels.OCR_CLICK_THROUGH,
              this.boxId,
              this._clickThrough
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

    // Listen to ENTER keys, remove the ENTER key blocker on the globalShortcuts, then re-add it afterwards, if scanAfterEnter is enabled.
    if (this.scanAfterEnter > 0) {
      SharedGlobalShortcuts.registerOnce(
        "ENTER",
        async () => {
          // registerOnce unregisters the ENTER key before this callback is activated, allowing us to re-trigger the ENTER key via the Python backend.
          // "Why not re-trigger the ENTER key in ElectronJS???" - We can't. Need to use external libraries like IOHook, which don't work anymore.
          await triggerEnterNodeFetch();

          if (this._timerScanAfterEnter)
            clearTimeout(this._timerScanAfterEnter);

          this._timerScanAfterEnter = setTimeout(async () => {
            console.log(
              "Scanning box after some time has passed with ENTER key being pressed..."
            );
            await this.scanAndTranslateBox();
          }, this.scanAfterEnter * 1000);
        },
        true
      ); // Set doReRegister to 'true' here, to re-register this exact callback after being triggered.
    }

    if (this.autoScan) {
      /*
        If auto scan is on, then every 3 seconds, take an image and compare it to the previous image taken for this box.
        If the previous image is found to be different than the new image (or the previous does not exist), then send it to the backend.
      */
      const SCAN_MS = 3000;

      // Can't do the faster scan here: the image similarity check is on the JS side, whereas the faster scan only creates the image on the Python side.
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

    if (
      this.activationKey !== DISABLED_KEY_VALUE &&
      this.serverSideActivationKey
    ) {
      this.rememberThisBox();

      if (this.ocrWindow !== null) {
        this.ocrWindow.on("moved", () => {
          // The API automatically overrides the box hotkey if the data is updated.
          this.rememberThisBox();
        });

        this.ocrWindow.on("resized", () => {
          // The API automatically overrides the box hotkey if the data is updated.
          this.rememberThisBox();
        });
      }
    }

    if (this.followsCursor) {
      this.follow();
    }

    if (this.listenAudio) {
      this.registerBoxListeningAudio();
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
    if (
      this.activationKey !== DISABLED_KEY_VALUE &&
      !this.serverSideActivationKey
    )
      SharedGlobalShortcuts.unregister(
        this.activationKey,
        this._activationKeyCallback
      );
    if (this.pauseKey !== DISABLED_KEY_VALUE)
      SharedGlobalShortcuts.unregister(this.pauseKey, this._pauseKeyCallback);
    if (this.hideKey !== DISABLED_KEY_VALUE)
      SharedGlobalShortcuts.unregister(this.hideKey, this._hideKeyCallback);
    if (this.followKey !== DISABLED_KEY_VALUE) {
      SharedGlobalShortcuts.unregister(this.followKey, this._followKeyCallback);
    }
    if (this.clickThroughKey !== DISABLED_KEY_VALUE)
      SharedGlobalShortcuts.unregister(
        this.clickThroughKey,
        this._clickThroughKeyCallback
      );
    if (this.spellingCorrectionKey !== DISABLED_KEY_VALUE)
      SharedGlobalShortcuts.unregister(
        this.spellingCorrectionKey,
        this._spellingCorrectionKeyCallback
      );
    if (this.scanAfterEnter > 0) {
      // BUG: Will bug out if there are multiple boxes with scanAfterEnter (should never happen though?)
      // 'null' here means we unregister ALL enter callbacks.
      SharedGlobalShortcuts.unregister("ENTER", null);
    }

    if (
      this.activationKey !== DISABLED_KEY_VALUE &&
      this.serverSideActivationKey
    ) {
      this.forgetThisBox();
    }

    if (this.listenAudio) {
      this.unregisterBoxListeningAudio();
    }

    if (this._timerAutoScan) clearInterval(this._timerAutoScan);
    if (this._timerClipboard) clearInterval(this._timerClipboard);
    if (this._timerScanAfterEnter) clearTimeout(this._timerScanAfterEnter);

    if (this._timerFollowsCursor) clearInterval(this._timerFollowsCursor);

    ipcMain.removeListener(
      "task3_image_grabbed",
      this._revealRecordingBoxesCallback
    );

    this._timerAutoScan = null;
    this._timerClipboard = null;
    this._timerScanAfterEnter = null;
    this._timerFollowsCursor = null;

    this._paused = false;
    this._hide = false;
    this._follow = false;
  }
}
