import React from "react";
import {
  TreeItem,
  TreeItemProps,
  treeItemClasses,
} from "@mui/x-tree-view/TreeItem";
import FileInfo from "../../../types/FileInfo";
import classNames from "classnames";
import { alpha, styled } from "@mui/material/styles";

const StyledTreeItem = styled((props: TreeItemProps) => (
  <TreeItem {...props} />
))(({ theme }) => ({
  [`& .${treeItemClasses.iconContainer}`]: {
    "& .close": {
      opacity: 0.3,
    },
  },
  [`& .${treeItemClasses.root}`]: {
    marginLeft: 15,
    paddingLeft: 18,
    borderLeft: `1px dashed ${alpha(theme.palette.text.primary, 0.4)}`,
  },
}));

type BaseFileItem = {
  fileName: string;
  fullPath: string;
  childrenItems: BaseFileItem[];
};

export type FileItemProps = BaseFileItem & {
  selectedPath?: string | null | undefined;
  onSelect: (f: FileInfo) => void;
  isRoot: boolean;
  onOpenMenu: (e: any, fullPath: string) => void;
  onRootSelect: () => void;
};

const trimFileName = (s: string) => {
  if (s.length > 20) {
    return `${s.substring(0, 20)}...`;
  } else return s;
};

const FileItemPane = ({
  fileName,
  fullPath,
  selectedPath,
  onSelect,
  childrenItems,
  isRoot,
  onOpenMenu,
  onRootSelect,
}: FileItemProps) => {
  const handleClick = () => {
    if (isRoot) return onRootSelect();

    onSelect({ fileName, fullPath, childrenItems });
  };

  const handleMenuOpen = (e: any) => {
    if (isRoot) return;

    e.stopPropagation();
    onOpenMenu(e, fullPath);
  };

  const divClasses = classNames({
    fileItem: true,
    fileItemRoot: isRoot,
    fileItemSelected: selectedPath === fullPath,
  });

  return (
    <StyledTreeItem
      itemId={fullPath}
      label={isRoot ? "Library" : trimFileName(fileName)}
      onClick={handleClick}
      className={divClasses}
      onContextMenu={handleMenuOpen}
      data-testid={`file-${fullPath}`}
      classes={
        isRoot
          ? {
              content: "file-root-header",
            }
          : undefined
      }
    >
      {childrenItems.map((c) => (
        <FileItemPane
          fileName={c.fileName}
          fullPath={c.fullPath}
          childrenItems={c.childrenItems}
          selectedPath={selectedPath}
          onSelect={onSelect}
          key={c.fullPath}
          isRoot={false}
          onOpenMenu={onOpenMenu}
          onRootSelect={onRootSelect}
        />
      ))}
    </StyledTreeItem>
  );
};

export default FileItemPane;
