import React, {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import { Box, Fade, Stack, SxProps, Typography } from "@mui/material";
import DragHandleIcon from "@mui/icons-material/DragHandle";
import { BoxOptionsFrontend } from "../../../types/BoxOptions";
import { MainGateway } from "../../../utils/mainGateway";

type OcrBoxPaneProps = BoxOptionsFrontend & {
  loading: boolean;
  text: string;
  sourceText: string | undefined;
  loadingOpacity: number;
  hide: boolean;
  pause: boolean;
  prevTexts: string[];
  boxId: string;
  hideHandle?: boolean;
  clickThrough: boolean;
  enableCuda: boolean;
};

const msToSecs = (ms: number) => (ms ? ms * 1000 : 300);

// Also from: https://stackoverflow.com/questions/1855884/determine-font-color-based-on-background-color
const hexToLuma = (color: string) => {
  const hex = color.replace(/#/, "");
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4), 16);

  const a =
    1.0 - [0.299 * r, 0.587 * g, 0.114 * b].reduce((a, b) => a + b) / 255;

  return a;
};

// From: https://gist.github.com/lopspower/03fb1cc0ac9f32ef38f4
const hexWithAlpha = (color: string, percentage: number) => {
  const decimal = `0${Math.round(255 * percentage).toString(16)}`
    .slice(-2)
    .toUpperCase();
  return color + decimal;
};

const TEXT_FIT_EVERY_MS = 500;

const OcrBoxPane = ({
  loading,
  text,
  textAlign,
  fontColor,
  fontSize,
  bionicReading,
  bold,
  backgroundColor,
  fadeAwayTime,
  backgroundOpacity,
  strokeColor,
  strokeSize,
  loadingOpacity,
  hide,
  pause,
  prevTexts,
  boxId,
  hideHandle,
  clickThrough,
  fullyDraggable,
  enableCuda,
  sourceText,
}: OcrBoxPaneProps) => {
  const [visible, setVisible] = useState(true);
  const [isHovering, setIsHovering] = useState(false);

  const [useLightHandle, setUseLightHandle] = useState(false);

  const [background, setBackground] = useState(
    hexWithAlpha(backgroundColor, backgroundOpacity)
  );

  const timer = useRef<any>(null);

  const [usingFontSize, setUsingFontSize] = useState<number>(
    parseInt(fontSize as string)
  );
  const [usingStrokeSize, setUsingStrokeSize] = useState<number>(strokeSize);

  const textRef = useRef<any>(null);
  const lastTextFitTime = useRef(Date.now());

  /** Give the user an informative "loading" text the very first time the box is loading (processing some text). */
  const [firstLoading, setFirstLoading] = useState(false);
  const firstLoadingDone = useRef(false);
  useEffect(() => {
    if (loading && !firstLoadingDone.current) {
      setFirstLoading(true);
    }

    if (!loading && firstLoading) {
      setFirstLoading(false);
      firstLoadingDone.current = true;
    }
  }, [loading, firstLoading]);

  // Prevent double-clicking from focusing text (annoying when trying to toggle handle color).
  // From: https://stackoverflow.com/questions/880512/prevent-text-selection-after-double-click
  useEffect(() => {
    const cb = (ev: MouseEvent) => {
      if (ev.detail > 1) {
        ev.preventDefault();
      }
    };

    document.addEventListener("mousedown", cb, false);

    return () => {
      document.removeEventListener("mousedown", cb);
    };
  }, []);

  useEffect(() => {
    if (!backgroundColor) return;

    setUseLightHandle(hexToLuma(backgroundColor) > 0.5);
  }, [backgroundColor]);

  const onHoverEnter = useCallback(() => {
    setIsHovering(true);
  }, []);

  const onHoverLeave = useCallback(() => {
    setIsHovering(false);
  }, []);

  useEffect(() => {
    setBackground(hexWithAlpha(backgroundColor, backgroundOpacity));
  }, [backgroundColor, backgroundOpacity]);

  useEffect(() => {
    // When text or loading state changes, briefly show the faded box if fade is enabled.
    if (fadeAwayTime > 0) {
      if (timer.current) clearTimeout(timer.current);

      setVisible(true);
      timer.current = setTimeout(
        () => setVisible(false),
        msToSecs(fadeAwayTime)
      );

      return () => {
        if (timer.current) clearTimeout(timer.current);
      };
    }
  }, [text, loading]);

  const getTextContent = useCallback(
    (t: string, firstLoad: boolean, cudaEnabled: boolean) => {
      if (firstLoad)
        return (
          <>
            <span>Loading the model. This may take a minute...</span>
            <br />
            <br />
            {!cudaEnabled && (
              <i>
                Have a good Nvidia GPU? Enable CUDA in the settings for faster
                processing!
              </i>
            )}
          </>
        );
      if (pause) return `${t} (PAUSED)`;
      return t;
    },
    [pause]
  );

  const renderText = useCallback(() => {
    const sourceTextComponent =
      !firstLoading && sourceText ? (
        <>
          <br />
          <br />
          <i
            style={{
              fontSize: Math.floor(usingFontSize * 0.75) + 1,
            }}
          >
            {sourceText}
          </i>
        </>
      ) : (
        <></>
      );

    if (bold) {
      return (
        <>
          <b>{getTextContent(text, firstLoading, enableCuda)}</b>
          {sourceTextComponent}
        </>
      );
    }

    if (!bionicReading || !text || text.length <= 1 || firstLoading) {
      return (
        <>
          {getTextContent(text, firstLoading, enableCuda)}
          {sourceTextComponent}
        </>
      );
    }

    const middleIndex = Math.floor(text.length / 2);
    const firstHalf = text.slice(0, middleIndex).split("");
    let secondHalf: any = text.slice(middleIndex);

    const firstHalfBold = firstHalf.map((char, index) => (
      <b key={`${char}_${index}`}>{char}</b>
    ));

    secondHalf = getTextContent(secondHalf, firstLoading, enableCuda);

    return (
      <>
        {firstHalfBold}
        {secondHalf}
        {sourceTextComponent}
      </>
    );
  }, [text, pause, firstLoading, enableCuda, sourceText, usingFontSize]);

  const fitTextInBox = useCallback(() => {
    if (!textRef.current) return;

    const minFontSize = 6;
    let curFontSize = parseInt(fontSize as string, 10);

    let curStrokeSize = strokeSize;

    textRef.current.style.fontSize = `${curFontSize}px`;
    textRef.current.style.WebkitTextStrokeWidth = `${curStrokeSize}px`;

    while (
      document.documentElement.scrollHeight >
      document.documentElement.clientHeight
    ) {
      curFontSize -= 1;
      curStrokeSize = Math.max(
        strokeSize * 0.4,
        curStrokeSize - strokeSize * 0.1
      );

      if (curFontSize <= minFontSize) {
        curFontSize = minFontSize;
        break;
      }

      textRef.current.style.fontSize = `${curFontSize}px`;
      textRef.current.style.WebkitTextStrokeWidth = `${curStrokeSize}px`;
    }

    setUsingFontSize(curFontSize);
    setUsingStrokeSize(curStrokeSize);
  }, [text, fontSize, strokeSize]);

  useLayoutEffect(() => {
    // Throttle instead of debounce.
    // !loading so we always fit the final result.

    const now = Date.now();
    if (!loading || now - lastTextFitTime.current >= TEXT_FIT_EVERY_MS) {
      fitTextInBox();
      lastTextFitTime.current = now;
    }
  }, [fitTextInBox, loading]);

  useEffect(() => {
    let debounce: any = undefined;

    const cb = () => {
      clearTimeout(debounce);
      debounce = setTimeout(() => {
        // Since "resize" window event is only called at the END of a resize (via the debounce), we reset the font size.
        fitTextInBox();
      }, 500);
    };

    window.addEventListener("resize", cb);

    return () => {
      clearTimeout(debounce);
      window.removeEventListener("resize", cb);
    };
  }, [fitTextInBox]);

  let textOpacity = pause ? 0.6 : 1;
  if (loading) textOpacity = loadingOpacity;

  const extraTextStyles: SxProps = {
    opacity: textOpacity,
    textAlign,
    color: `${fontColor} !important`,
    fontSize: usingFontSize,
    WebkitTextStrokeWidth: `${usingStrokeSize}px`,
    WebkitTextStrokeColor: strokeColor,
    fontFamily: '"ocrbox.otf", "ocrbox.ttf", Roboto, "Roboto", Arial',
    paintOrder: "stroke fill", // Necessary for pretty strokes.
    whiteSpace: "pre-line", // May have side effects. TODO: Monitor.
  };

  const extraPrevTextStyles: SxProps = {
    opacity: textOpacity - 0.25,
    textAlign,
    color: `${fontColor} !important`,
    fontSize: Math.floor(usingFontSize * 0.75),
    WebkitTextStrokeWidth: `${usingStrokeSize}px`,
    WebkitTextStrokeColor: strokeColor,
    fontFamily: '"ocrbox.otf", "ocrbox.ttf", Roboto, "Roboto", Arial',
    paintOrder: "stroke fill", // Necessary for pretty strokes.
    whiteSpace: "pre-line", // May have side effects. TODO: Monitor.
  };

  const extraBoxStyles: SxProps = {
    background,
  };

  // If options wasn't given, render null.
  if (!fontSize || hide) {
    return null;
  }

  const backgroundHidden = backgroundOpacity <= 0.05;

  const onDoubleClick = () => {
    if (!backgroundHidden) return;

    setUseLightHandle((prev) => !prev);
  };

  const getHandleOpacity = () => {
    if (clickThrough) {
      return 0.0;
    }

    return backgroundHidden ? 0.75 : 0.1;
  };

  let boxWindowClasses = "fullBoxApp";
  // if (true) boxWindowClasses += " draggableWindow";

  return (
    <div
      className={boxWindowClasses}
      onMouseOver={onHoverEnter}
      onMouseOut={onHoverLeave}
      style={{ opacity: hide ? 0 : 1 }}
      onDoubleClick={onDoubleClick}
    >
      <Fade
        in={visible || isHovering || loading}
        timeout={{ enter: 300, appear: 300, exit: 600 }}
        unmountOnExit
      >
        <Box
          className={fullyDraggable ? "boxAppFullyDraggable" : "boxApp"}
          sx={extraBoxStyles}
        >
          <div className="boxAppHandleTopLeft" />
          <Stack spacing={1} className="boxText">
            {prevTexts.map((x, ind) => (
              <Typography
                variant="body2"
                sx={extraPrevTextStyles}
                align={textAlign as any}
                key={ind.toString() + x}
              >
                {x}
              </Typography>
            ))}
            <Typography
              variant="body1"
              sx={extraTextStyles}
              align={textAlign as any}
              ref={textRef}
            >
              {renderText()}
            </Typography>
          </Stack>
          <div className="boxAppHandleTopRight" />
          <div className="boxAppHandleBottomLeft" />
          {!hideHandle && (
            <div className="boxAppHandleBottomRight">
              <DragHandleIcon
                className={
                  useLightHandle ? "boxAppHandleIcon" : "boxAppHandleIconDark"
                }
                sx={{ opacity: getHandleOpacity() }}
              />
            </div>
          )}
        </Box>
      </Fade>
    </div>
  );
};

export default OcrBoxPane;
