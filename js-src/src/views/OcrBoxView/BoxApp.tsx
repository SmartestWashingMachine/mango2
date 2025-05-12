import React, { useEffect, useState } from "react";
import { CssBaseline } from "@mui/material";
import OcrBoxPane from "./components/BoxPane";
import {
  listenTask3Updates,
  triggerEnter,
} from "../../flaskcomms/ocrBoxFrontendComms";
import { BoxOptionsFrontend } from "../../types/BoxOptions";
import { MainGateway } from "../../utils/mainGateway";

const CLIPBOARD_COPY_DEFAULT_TEXT =
  `I will automatically translate text found in the clipboard. Use the bottom right handle to drag me around!`.trim();
const ACTIVATE_DEFAULT_TEXT = (k: string) =>
  `I will automatically translate anything behind me when "${k}" is pressed. Use the bottom right handle to drag me around!`.trim();

const ACTIVATE_ADVANCED_TEXT = (k: string, l: string) =>
  `I will automatically translate anything behind me when "${k}" is pressed. Hide me with "${l}" before translating!`.trim();

const MISC_DEFAULT_TEXT = "Translated text will show here.";

export type BoxAppProps = {
  boxId: string;
};

const sliceArrIgnorePlaceHolders = (
  arr: string[],
  start: number,
  end?: number
) => {
  return arr
    .slice(start, end)
    .filter(
      (x) =>
        x !== MISC_DEFAULT_TEXT &&
        !x.startsWith("I will automatically translate")
    );
};

const getLastAndOthersInArr = (arr: string[]) => {
  if (arr.length === 0) return ["", []] as [string, string[]];
  if (arr.length === 1) return [arr[0], []] as [string, string[]];

  return [arr[arr.length - 1], arr.slice(0, arr.length - 1)] as [
    string,
    string[]
  ];
};

const BoxApp = ({ boxId }: BoxAppProps) => {
  // Output target text.
  const [text, setText] = useState<string[]>([]);

  const [loading, setLoading] = useState(false);
  const [options, setOptions] = useState<BoxOptionsFrontend | null>(null);

  const [removeSpeaker, setRemoveSpeaker] = useState(false);
  const [useStream, setUseStream] = useState(false);

  const [hide, setHide] = useState(false);
  const [pause, setPause] = useState(false);
  const [clickThrough, setClickThrough] = useState(false);

  const [autoEnterTimerId, setAutoEnterTimerId] =
    useState<NodeJS.Timeout | null>();
  const [autoEnterTime, setAutoEnterTime] = useState<number | null>(null);

  const [append, setAppend] = useState(false);

  useEffect(() => {
    document.body.style.backgroundColor = "rgba(255, 255, 255, 0.0)"; // for fade-in. this gives a transparent window.
  }, []);

  useEffect(() => {
    const beginCb = () => {
      setLoading(true);

      if (append) {
        const maxQueue = 3;
        setText((t) =>
          t.length > maxQueue
            ? [...sliceArrIgnorePlaceHolders(t, 1), ""]
            : [...t, ""]
        );
      }
    };

    const doneCb = (values: string[], sourceValues: string[]) => {
      let newText: any = values.join("\n");
      if (removeSpeaker) {
        newText = newText.split(":", 2);
        newText = newText[newText.length - 1].trim();
      }

      if (newText && newText.length > 0) {
        if (append) {
          setText((t) => [...sliceArrIgnorePlaceHolders(t, 0, -1), newText]);
        } else {
          setText([newText]);
        }
      }
      setLoading(false);
    };

    const streamCb = (values: string) => {
      // May act weird with removeSpeaker / task3...
      if (!values || values.length === 0) return;

      if (append) {
        setText((t) => [...sliceArrIgnorePlaceHolders(t, 0, -1), values]);
      } else {
        setText([values]);
      }
    };

    const connectCb = async () => {
      await MainGateway.connectedOcrBox(boxId, true);
    };

    const disconnectCb = async () => {
      await MainGateway.connectedOcrBox(boxId, false);
    };

    const socket = listenTask3Updates(
      boxId,
      beginCb,
      doneCb,
      streamCb,
      connectCb,
      disconnectCb
    );

    const cleanup = () => {
      socket.disconnect();
    };

    window.addEventListener("beforeunload", cleanup);

    return () => {
      window.removeEventListener("beforeunload", cleanup);
      cleanup();
    };
  }, [removeSpeaker, useStream, boxId]);

  useEffect(() => {
    if (!loading && autoEnterTime !== null && autoEnterTime > 0) {
      const timerId = setTimeout(() => {
        triggerEnter();
        setAutoEnterTimerId(null);
      }, autoEnterTime * 1000);

      setAutoEnterTimerId(timerId);
    }
  }, [loading, autoEnterTime]);

  useEffect(() => {
    if (loading && autoEnterTimerId) {
      clearTimeout(autoEnterTimerId);
      setAutoEnterTimerId(null);
    }

    return () => {
      if (autoEnterTimerId) {
        clearTimeout(autoEnterTimerId);
      }
    };
  }, [loading, autoEnterTimerId]);

  /**
   * Retrieve initial box data from the electron backend.
   */
  useEffect(() => {
    const w = window as any;
    let didCancel = false;

    const asyncCb = async () => {
      const data = await w.electronAPI.getStoreData();

      if (didCancel || !data) return;

      const boxOptions = data.boxes.find((o: any) => o.boxId === boxId);
      if (boxOptions) {
        setOptions(boxOptions);
        setRemoveSpeaker(boxOptions?.removeSpeaker);
        setUseStream(boxOptions?.useStream);
        setAutoEnterTime(boxOptions?.autoEnterTime);
        setAppend(boxOptions?.append);

        if (boxOptions.listenClipboard) {
          setText([CLIPBOARD_COPY_DEFAULT_TEXT]);
        } else if (boxOptions.activationKey !== "Escape") {
          if (boxOptions.serverSideActivationKey) {
            setText([
              ACTIVATE_ADVANCED_TEXT(
                boxOptions.activationKey,
                boxOptions.hideKey
              ),
            ]);
          } else setText([ACTIVATE_DEFAULT_TEXT(boxOptions.activationKey)]);
        } else {
          setText([MISC_DEFAULT_TEXT + ` (Box Name: ${boxOptions.boxId})`]);
        }
      }
    };

    asyncCb();

    return () => {
      didCancel = true;
    };
  }, []);

  /**
   * Listen and update the box visuals if the box data from the electron backend is updated.
   */
  /*
  useEffect(() => {
    const w = window as any;

    const cb = (s: any) => {
      if (!s) return;

      const boxOptions = s.boxes.find((o: any) => o.boxId === boxId);
      if (boxOptions) {
        setOptions(boxOptions);
        setRemoveSpeaker(boxOptions?.removeSpeaker);
        setUseStream(boxOptions?.useStream);
      }
    };

    const removeCb = w.electronAPI.listenStoreDataChange(cb);

    const cleanup = () => {
      removeCb();
    };

    window.addEventListener("beforeunload", cleanup);

    return () => {
      window.removeEventListener("beforeunload", cleanup);
      cleanup();
    };
  }, []);
  */

  useEffect(() => {
    const hideCb = (e: any, bId: string, hid: boolean) => {
      if (boxId === bId) setHide(hid);
    };
    const removeHideCb = MainGateway.listenOcrHideChange(hideCb);

    const clickThroughCb = (e: any, bId: string, ct: boolean) => {
      if (boxId === bId) setClickThrough(ct);
    };
    const removeClickThroughCb =
      MainGateway.listenOcrClickThroughChange(clickThroughCb);

    const cleanup = () => {
      removeHideCb();
      removeClickThroughCb();
    };

    window.addEventListener("beforeunload", cleanup);

    return () => {
      window.removeEventListener("beforeunload", cleanup);
      cleanup();
    };
  }, []);

  useEffect(() => {
    const cb = (e: any, bId: string, paused: boolean) => {
      if (boxId === bId) setPause(paused);
    };
    const removeCb = MainGateway.listenOcrPauseChange(cb);

    const cleanup = () => {
      removeCb();
    };

    window.addEventListener("beforeunload", cleanup);

    return () => {
      window.removeEventListener("beforeunload", cleanup);
      cleanup();
    };
  }, []);

  if (!options) return <div></div>;

  const [curText, prevTexts] = getLastAndOthersInArr(text);

  return (
    <CssBaseline>
      <OcrBoxPane
        loading={loading}
        text={curText}
        prevTexts={prevTexts}
        {...options}
        loadingOpacity={useStream ? 0.75 : 0.25}
        pause={pause}
        hide={hide}
        boxId={boxId} // TODO: Refactor MainGateway to only be called here, thus dispensing of boxId in OcrBoxPane.
        clickThrough={clickThrough}
      />
    </CssBaseline>
  );
};

export default BoxApp;
