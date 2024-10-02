import React, { useEffect, useRef, useState } from "react";
import { Paper, Typography } from "@mui/material";
import IHistoryText from "../../../types/HistoryText";
import HistoryItem from "./HistoryItem";
import ChatBubbleOutlineIcon from "@mui/icons-material/ChatBubbleOutline";
import HistoryContextMenu from "./HistoryContextMenu";
import { Virtuoso } from "react-virtuoso";

type HistoryPaneProps = {
  texts: IHistoryText[];
  selectedIds: string[];
  onSelectItem: (uuid: string) => void;
  initialItemCount?: number;
  isBrief?: boolean;
};

const HistoryPane = ({
  texts,
  onSelectItem,
  selectedIds,
  initialItemCount,
  isBrief,
}: HistoryPaneProps) => {
  // These values are for the context menu.
  const [isOpen, setIsOpen] = useState(false);
  const [x, setX] = useState(0);
  const [y, setY] = useState(0);

  const [selSourceText, setSelSourceText] = useState("");
  const [selTargetText, setSelTargetText] = useState("");

  const handleClose = () => {
    setIsOpen(false);
  };

  const handleContextMenu = (
    e: React.MouseEvent,
    sourceText: string,
    targetText: string
  ) => {
    e.preventDefault();

    const newIsOpen = !isOpen;

    setIsOpen(newIsOpen);

    if (newIsOpen) {
      // Values from: https://mui.com/material-ui/react-menu/#context-menu
      setX(e.clientX + 2);
      setY(e.clientY - 6);

      setSelSourceText(sourceText);
      setSelTargetText(targetText);
    }
  };

  // ref is for auto scrolling.
  const ref = useRef<any | null>(null);

  const textItemsData = texts.map((t, index) => ({
    sourceText: t.sourceText,
    targetText: t.targetText,
    isLast: index === texts.length - 1,
    isSelected: selectedIds.indexOf(t.uuid) > -1,
    onClick: () => onSelectItem(t.uuid),
    onContextMenu: handleContextMenu,
    key: t.uuid,
    sourceTokens: t.sourceTokens,
    targetTokens: t.targetTokens,
    attentions: t.attentions,
    otherTargetTexts: t.otherTargetTexts,
  }));

  return (
    <Paper square elevation={2} className="historyList">
      {
        texts.length === 0 ? (
          <div className="emptyHistoryImage">
            <ChatBubbleOutlineIcon
              color="info"
              className="emptyHistoryImageInner"
            />
            <Typography
              variant="h5"
              align="center"
              sx={{ color: "hsl(291, 2%, 88%)" }}
            >
              Backlog empty.
            </Typography>
            <Typography
              variant="body2"
              align="center"
              sx={{ color: "hsl(291, 3%, 74%)" }}
            >
              Try typing a sentence below!
            </Typography>
          </div>
        ) : initialItemCount ? (
          <Virtuoso
            style={{ height: "100%" }}
            totalCount={textItemsData.length}
            itemContent={(index) => <HistoryItem {...textItemsData[index]} isBrief={isBrief} />}
            ref={ref}
            initialItemCount={initialItemCount || undefined}
            followOutput={() => true}
          />
        ) : (
          <Virtuoso
            style={{ height: "100%" }}
            totalCount={textItemsData.length}
            itemContent={(index) => <HistoryItem {...textItemsData[index]} isBrief={isBrief} />}
            ref={ref}
            followOutput={() => true}
          />
        ) // React virtuoso still sets initialItemCount if undefined... very annoying.
      }
      <HistoryContextMenu
        x={x}
        y={y}
        isOpen={isOpen}
        onClose={handleClose}
        sourceText={selSourceText}
        targetText={selTargetText}
      />
    </Paper>
  );
};

export default HistoryPane;
