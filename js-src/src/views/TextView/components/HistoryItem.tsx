import React from "react";
import { ListItem, ListItemButton, ListItemText } from "@mui/material";

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
}: HistoryItemProps) => {
  const targetText = targetTextList[0];

  const handleContextMenu = (e: React.MouseEvent) => {
    onContextMenu(e, sourceText, targetText);
  };

  return (
    <ListItem dense divider={!isLast}>
      <ListItemButton onClick={onClick} onContextMenu={handleContextMenu}>
        <ListItemText
          secondaryTypographyProps={{
            sx: {
              color: isSelected ? "#ce93d8" : "rgba(255, 255, 255, 0.7)",
            },
          }}
          sx={{ overflowWrap: "break-word" }}
          primary={<>{targetText}</>}
          secondary={<>{sourceText}</>}
        />
      </ListItemButton>
    </ListItem>
  );
};

export default HistoryItem;
