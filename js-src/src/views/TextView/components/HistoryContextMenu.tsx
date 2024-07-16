import { Menu, MenuItem } from "@mui/material";
import React, { useState } from "react";

export type HistoryContextMenuProps = {
  x: number;
  y: number;
  isOpen: boolean;
  onClose: () => void;
  sourceText: string;
  targetText: string;
};

const HistoryContextMenu = ({
  x,
  y,
  isOpen,
  onClose,
  sourceText,
  targetText,
}: HistoryContextMenuProps) => {
  const handleCopySource = () => {
    navigator.clipboard.writeText(sourceText);
    onClose();
  };

  const handleCopyTranslation = () => {
    navigator.clipboard.writeText(targetText);
    onClose();
  };

  return (
    <Menu
      open={isOpen}
      onClose={onClose}
      anchorReference="anchorPosition"
      anchorPosition={isOpen !== null ? { top: y, left: x } : undefined}
    >
      <MenuItem onClick={handleCopySource}>Copy Source</MenuItem>
      <MenuItem onClick={handleCopyTranslation}>Copy Translation</MenuItem>
    </Menu>
  );
};

export default HistoryContextMenu;
