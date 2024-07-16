import React, { useState } from "react";
import {
  ClickAwayListener,
  IconButton,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Paper,
} from "@mui/material";
import FileItemPane from "./FileItemPane";
import FileInfo from "../../../types/FileInfo";
import { SimpleTreeView } from "@mui/x-tree-view";
import RefreshIcon from "@mui/icons-material/Refresh";
import ArrowBackIosNewIcon from "@mui/icons-material/ArrowBackIosNew";
import FolderIcon from "@mui/icons-material/Folder";
import { MainGateway } from "../../../utils/mainGateway";

type FileListPaneProps = {
  rootItem: FileInfo | null;
  selectedPath: string | null;
  onSelectFileInfo: (f: FileInfo) => void;
  onRefresh: () => void;
  children?: any;
  onBackClick?: () => void;
  expandedItems?: string[];
};

const FileListPane = ({
  rootItem,
  selectedPath,
  onSelectFileInfo,
  onRefresh,
  children,
  onBackClick,
  expandedItems,
}: FileListPaneProps) => {
  const [menuOpenFor, setMenuOpenFor] = useState<string | null>(null); // a file's fullPath or null.
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);

  const handleMenuOpen = (e: any, fullPath: string) => {
    setMenuOpenFor(fullPath);
    setAnchorEl(e.target);
  };
  const handleMenuClose = () => setMenuOpenFor(null);

  /** Show the file in the explorer. */
  const handleShowFileClick = async () => {
    if (!menuOpenFor) return;

    await MainGateway.showFile(menuOpenFor);
    handleMenuClose();
  };

  return (
    <Paper className="filesListContainer" elevation={1}>
      <Paper className="filesListControls" elevation={3}>
        <IconButton
          onClick={onRefresh}
          className="filesListRefresh"
          data-testid="refresh-button"
          sx={{ opacity: 0.85 }}
        >
          <RefreshIcon />
        </IconButton>
        {children}
        <IconButton
          onClick={onBackClick}
          className="filesListRefresh"
          data-testid="back-button"
          sx={{ opacity: 0.85 }}
        >
          <ArrowBackIosNewIcon />
        </IconButton>
      </Paper>
      <SimpleTreeView
        selectedItems={selectedPath || ""}
        className="filesList"
        sx={{ height: 240, flexGrow: 1, maxWidth: 400, overflowY: "auto" }}
        expandedItems={expandedItems || undefined}
      >
        {rootItem && (
          <FileItemPane
            fileName={rootItem.fileName}
            fullPath={rootItem.fullPath}
            childrenItems={rootItem.childrenItems}
            selectedPath={selectedPath}
            onSelect={onSelectFileInfo}
            isRoot
            onOpenMenu={handleMenuOpen}
          />
        )}
        {!rootItem && (
          <FileItemPane
            fileName="Loading..."
            fullPath="loading"
            childrenItems={[]}
            selectedPath={selectedPath}
            onSelect={() => {}}
            isRoot
            onOpenMenu={() => {}}
          />
        )}
      </SimpleTreeView>
      <ClickAwayListener onClickAway={handleMenuClose}>
        <Menu
          anchorEl={anchorEl}
          open={!!menuOpenFor}
          onClose={handleMenuClose}
        >
          <MenuItem
            onClick={handleShowFileClick}
            data-testid="file-show-button"
          >
            <ListItemIcon>
              <FolderIcon />
            </ListItemIcon>
            <ListItemText primary="Open In Explorer" />
          </MenuItem>
        </Menu>
      </ClickAwayListener>
    </Paper>
  );
};

export default FileListPane;
