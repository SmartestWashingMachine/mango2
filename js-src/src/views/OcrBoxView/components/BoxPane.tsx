import React, { useCallback, useEffect, useRef, useState } from "react";
import { Box, Fade, Stack, SxProps, Typography } from "@mui/material";
import DragHandleIcon from "@mui/icons-material/DragHandle";
import { BoxOptionsFrontend } from "../../../types/BoxOptions";
import { MainGateway } from "../../../utils/mainGateway";

type OcrBoxPaneProps = BoxOptionsFrontend & {
  loading: boolean;
  text: string;
  loadingOpacity: number;
  hide: boolean;
  pause: boolean;
  prevTexts: string[];
  boxId: string;
  hideHandle?: boolean;
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

const OcrBoxPane = ({
  loading,
  text,
  textAlign,
  fontColor,
  fontSize,
  bionicReading,
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
}: OcrBoxPaneProps) => {
  const [visible, setVisible] = useState(true);
  const [isHovering, setIsHovering] = useState(false);

  const [useLightHandle, setUseLightHandle] = useState(false);

  const [background, setBackground] = useState(
    hexWithAlpha(backgroundColor, backgroundOpacity)
  );

  const timer = useRef<any>(null);

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
    // When text changes, briefly show the faded box if fade is enabled.
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
  }, [text]);

  const renderText = useCallback(() => {
    if (!bionicReading || !text || text.length <= 1) {
      if (pause) return `${text} (PAUSED)`;
      return text;
    }

    const middleIndex = Math.floor(text.length / 2);
    const firstHalf = text.slice(0, middleIndex).split("");
    let secondHalf = text.slice(middleIndex);

    const firstHalfBold = firstHalf.map((char, index) => (
      <b key={`${char}_${index}`}>{char}</b>
    ));

    if (pause) secondHalf += " (PAUSED)";

    return (
      <>
        {firstHalfBold}
        {secondHalf}
      </>
    );
  }, [text, pause]);

  let textOpacity = pause ? 0.6 : 1;
  if (loading) textOpacity = loadingOpacity;

  const extraTextStyles: SxProps = {
    opacity: textOpacity,
    textAlign,
    color: `${fontColor} !important`,
    fontSize,
    WebkitTextStrokeWidth: `${strokeSize}px`,
    WebkitTextStrokeColor: strokeColor,
    fontFamily: '"ocrbox.otf", "ocrbox.ttf", Roboto, "Roboto", Arial',
    paintOrder: "stroke fill", // Necessary for pretty strokes.
  };

  const extraPrevTextStyles: SxProps = {
    opacity: textOpacity - 0.25,
    textAlign,
    color: `${fontColor} !important`,
    fontSize: Math.floor(parseInt(fontSize as string) * 0.75),
    WebkitTextStrokeWidth: `${strokeSize}px`,
    WebkitTextStrokeColor: strokeColor,
    fontFamily: '"ocrbox.otf", "ocrbox.ttf", Roboto, "Roboto", Arial',
    paintOrder: "stroke fill", // Necessary for pretty strokes.
  };

  const extraBoxStyles: SxProps = {
    background,
  };

  const timeoutMs = msToSecs(fadeAwayTime);

  // If options wasn't given, render null.
  if (!fontSize || hide) {
    return null;
  }

  const backgroundHidden = backgroundOpacity <= 0.05;

  const onDoubleClick = () => {
    if (!backgroundHidden) return;

    setUseLightHandle((prev) => !prev);
  };

  return (
    <div
      className="fullBoxApp"
      onMouseOver={onHoverEnter}
      onMouseOut={onHoverLeave}
      style={{ opacity: hide ? 0 : 1 }}
      onDoubleClick={onDoubleClick}
    >
      <Fade
        in={visible || isHovering}
        timeout={{ enter: 300, appear: 300, exit: timeoutMs }}
      >
        <Box className="boxApp" sx={extraBoxStyles}>
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
                sx={{ opacity: backgroundHidden ? 0.75 : 0.1 }}
              />
            </div>
          )}
        </Box>
      </Fade>
    </div>
  );
};

export default OcrBoxPane;
