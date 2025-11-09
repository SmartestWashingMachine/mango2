import React from "react";
import {
  Fade,
  IconButton,
  ListItem,
  ListItemButton,
  ListItemText,
  Stack,
} from "@mui/material";
import {
  ThumbDown,
  ThumbDownOutlined,
  ThumbUp,
  ThumbUpOutlined,
} from "@mui/icons-material";

type ColorState = {
  r: number;
  g: number;
  b: number;
};

const startColor: ColorState = {
  r: 128,
  g: 128,
  b: 128,
};

const endColor: ColorState = {
  r: 255,
  g: 255,
  b: 0,
};

// Grows fast then slows down.
const colorFastVal = (
  prop: keyof ColorState,
  colorA: ColorState,
  colorB: ColorState,
  intVal: number
) => {
  const coef = intVal / Math.cbrt(intVal);
  return Math.round(colorA[prop] * (1 - coef) + colorB[prop] * coef);
};

const colorInterpolate = (
  intVal: number,
  colorA: ColorState = startColor,
  colorB: ColorState = endColor
) => {
  return {
    r: colorFastVal("r", colorA, colorB, intVal),
    g: colorFastVal("g", colorA, colorB, intVal),
    b: colorFastVal("b", colorA, colorB, intVal),
  };
};

const maxColor = colorInterpolate(1);

type HistoryItemProps = {
  sourceText: string;
  targetText: string[]; // Legacy bug. Actually returns a list with 1 element.
  isLast: boolean;
  onClick: () => void;
  isSelected: boolean;
  onContextMenu: (
    e: React.MouseEvent,
    sourceText: string,
    targetText: string
  ) => void;
  attentions: number[][]; // Dim 0 = target. Dim 1 = source.
  sourceTokens: string[];
  targetTokens: string[];
  otherTargetTexts: string[];
  isBrief?: boolean;
  onRecommend: (index: number, recommended: boolean) => void;
  index: number;
};

const HistoryItem = ({
  sourceText,
  targetText: targetTextList,
  isLast,
  onClick,
  isSelected,
  onContextMenu,
  attentions,
  sourceTokens,
  targetTokens,
  otherTargetTexts,
  isBrief,
  onRecommend,
  index,
}: HistoryItemProps) => {
  const targetText = targetTextList[0];

  const handleContextMenu = (e: React.MouseEvent) => {
    onContextMenu(e, sourceText, targetText);
  };

  const [recommended, setRecommended] = React.useState(0);

  const handleRecommend = (e: any) => {
    e.preventDefault();
    e.stopPropagation();

    if (recommended !== 0) return;

    setRecommended(1);
    onRecommend(index, true);
  };

  const handleNotRecommend = (e: any) => {
    e.preventDefault();
    e.stopPropagation();

    if (recommended !== 0) return;

    setRecommended(2);
    onRecommend(index, false);
  };

  const renderRecommend = () =>
    recommended === 1 ? (
      <IconButton
        sx={{
          marginLeft: "auto",
        }}
        color="primary"
      >
        <ThumbUp sx={{ fontSize: "16px !important" }} />
      </IconButton>
    ) : (
      <IconButton
        onClick={handleRecommend}
        sx={{
          marginLeft: "auto",
        }}
        color="info"
      >
        <ThumbUpOutlined sx={{ fontSize: "16px !important" }} />
      </IconButton>
    );

  const renderNotRecommend = () =>
    recommended === 2 ? (
      <IconButton
        sx={{
          marginLeft: "auto",
        }}
        color="error"
      >
        <ThumbDown sx={{ fontSize: "16px !important" }} />
      </IconButton>
    ) : (
      <IconButton
        onClick={handleNotRecommend}
        sx={{
          marginLeft: "auto",
        }}
        color="info"
      >
        <ThumbDownOutlined sx={{ fontSize: "16px !important" }} />
      </IconButton>
    );

  const [hovering, setHovering] = React.useState(false);

  const handleHoverEnter = () => {
    setHovering(true);
  };

  const handleHoverLeave = () => {
    setHovering(false);
  };

  return (
    <ListItem
      dense
      divider={!isLast && !isBrief}
      onMouseEnter={handleHoverEnter}
      onMouseLeave={handleHoverLeave}
    >
      <Stack spacing={0.5} sx={{ width: "100%" }}>
        <ListItemButton
          onClick={onClick}
          onContextMenu={handleContextMenu}
          disableRipple
          sx={{ borderRadius: "2px" }} // For a better outline when hovering over.
        >
          <ListItemText
            secondaryTypographyProps={{
              sx: {
                color: isSelected ? "#ce93d8" : "rgba(255, 255, 255, 0.7)",
              },
            }}
            sx={{ overflowWrap: "break-word" }}
            primary={<>{targetText}</>}
            secondary={
              isBrief ? undefined : (
                <Stack direction="row" sx={{ width: "100%" }}>
                  {sourceText}
                  <Fade unmountOnExit={false} in={hovering} timeout={200}>
                    <Stack
                      direction="row"
                      spacing={0.5}
                      style={{ marginLeft: "auto" }}
                    >
                      {renderRecommend()}
                      {renderNotRecommend()}
                    </Stack>
                  </Fade>
                </Stack>
              )
            }
          />
        </ListItemButton>
      </Stack>
    </ListItem>
  );
};

export default HistoryItem;
