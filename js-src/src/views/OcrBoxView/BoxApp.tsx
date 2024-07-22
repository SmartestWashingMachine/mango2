import React, { useEffect, useState } from "react";
import { CssBaseline } from "@mui/material";
import OcrBoxPane from "./components/BoxPane";
import { listenTask3Updates } from "../../flaskcomms/ocrBoxFrontendComms";
import { BoxOptionsFrontend } from "../../types/BoxOptions";
import { MainGateway } from "../../utils/mainGateway";

const CLIPBOARD_COPY_DEFAULT_TEXT =
  `I will automatically translate text found in the clipboard. Use the bottom right handle to drag me around!`.trim();
const ACTIVATE_DEFAULT_TEXT = (k: string) =>
  `I will automatically translate anything behind me when "${k}" is pressed. Use the bottom right handle to drag me around!`.trim();
const MISC_DEFAULT_TEXT = "...";

export type BoxAppProps = {
  boxId: string;
};

const BoxApp = ({ boxId }: BoxAppProps) => {
  // Output target text.
  const [text, setText] = useState("");

  const [loading, setLoading] = useState(false);
  const [options, setOptions] = useState<BoxOptionsFrontend | null>(null);

  const [removeSpeaker, setRemoveSpeaker] = useState(false);
  const [useStream, setUseStream] = useState(false);

  const [hide, setHide] = useState(false);
  const [pause, setPause] = useState(false);

  useEffect(() => {
    document.body.style.backgroundColor = "rgba(255, 255, 255, 0.0)"; // for fade-in. this gives a transparent window.
  }, []);

  useEffect(() => {
    const beginCb = () => {
      setLoading(true);
    };

    const doneCb = (values: string[], sourceValues: string[]) => {
      let newText: any = values.join("\n");
      if (removeSpeaker) {
        newText = newText.split(":", 2);
        newText = newText[newText.length - 1].trim();
      }

      if (newText && newText.length > 0) {
        setText(newText);
      }
      setLoading(false);
    };

    const streamCb = (values: string) => {
      // May act weird with removeSpeaker / task3...
      if (!values || values.length === 0) return;

      setText(values);
    };

    const connectCb = async () => {
      await MainGateway.connectedOcrBox(boxId, true);
    };

    const disconnectCb = async () => {
      await MainGateway.connectedOcrBox(boxId, false);
    };

    const socket = listenTask3Updates(boxId, beginCb, doneCb, streamCb, connectCb, disconnectCb);

    const cleanup = () => {
      socket.disconnect();
    };

    window.addEventListener("beforeunload", cleanup);

    return () => {
      window.removeEventListener("beforeunload", cleanup);
      cleanup();
    };
  }, [removeSpeaker, useStream, boxId]);

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

        if (boxOptions.listenClipboard) {
          setText(CLIPBOARD_COPY_DEFAULT_TEXT);
        } else if (boxOptions.activationKey !== "Escape") {
          setText(ACTIVATE_DEFAULT_TEXT(boxOptions.activationKey));
        } else {
          setText(MISC_DEFAULT_TEXT);
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
    const cb = (e: any, bId: string, hid: boolean) => {
      if (boxId === bId) setHide(hid);
    };
    const removeCb = MainGateway.listenOcrHideChange(cb);

    const cleanup = () => {
      removeCb();
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

  return (
    <CssBaseline>
      <OcrBoxPane
        loading={loading}
        text={text}
        {...options}
        loadingOpacity={useStream ? 0.75 : 0.25}
        pause={pause}
        hide={hide}
      />
    </CssBaseline>
  );
};

export default BoxApp;
