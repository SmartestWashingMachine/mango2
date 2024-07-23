import React, { useCallback, useEffect, useRef, useState } from "react";
import { Box, Fade, SxProps, Typography } from "@mui/material";
import DragHandleIcon from "@mui/icons-material/DragHandle";
import { BoxOptionsFrontend } from "../../../types/BoxOptions";

type OcrBoxPaneProps = BoxOptionsFrontend & {
  loading: boolean;
  text: string;
  loadingOpacity: number;
  hide: boolean;
  pause: boolean;
};

const msToSecs = (ms: number) => (ms ? ms * 1000 : 300);

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
}: OcrBoxPaneProps) => {
  const [visible, setVisible] = useState(true);
  const [isHovering, setIsHovering] = useState(false);

  const [background, setBackground] = useState(hexWithAlpha(backgroundColor, backgroundOpacity));

  const timer = useRef<any>(null);

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
  };

  const extraBoxStyles: SxProps = {
    background,
  };

  const timeoutMs = msToSecs(fadeAwayTime);

  // If options wasn't given, render null.
  if (!fontSize || hide) {
    return null;
  }
  return (
    <div
      className="fullBoxApp"
      onMouseOver={onHoverEnter}
      onMouseOut={onHoverLeave}
    >
      <Fade
        in={visible || isHovering}
        timeout={{ enter: 300, appear: 300, exit: timeoutMs }}
      >
        <Box className="boxApp" sx={extraBoxStyles}>
          <div className="boxAppHandleTopLeft" />
          <Typography
            variant="body1"
            className="boxText"
            sx={extraTextStyles}
            align={textAlign as any}
          >
            {renderText()}
          </Typography>
          <div className="boxAppHandleTopRight" />
          <div className="boxAppHandleBottomLeft" />
          <div className="boxAppHandleBottomRight">
            <DragHandleIcon className="boxAppHandleIcon" />
          </div>
        </Box>
      </Fade>
    </div>
  );
};

export default OcrBoxPane;
