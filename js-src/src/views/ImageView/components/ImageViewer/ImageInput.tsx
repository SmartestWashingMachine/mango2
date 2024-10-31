import React, { useCallback } from "react";
import FolderIcon from "@mui/icons-material/Folder";
import { Typography, Paper, Stack, Collapse } from "@mui/material";
import { useDropzone } from "react-dropzone";
import classNames from "classnames";
import ImageProgressList from "./ImageProgressList";
import BaseView from "../../../BaseView";

type ImageInputProps = {
  onFilesSelected: (d: any) => void;
  selectDisabled: boolean;
  loadingProgress: number;
  pendingImageNames: string[];
  helperText?: string;
  rightPane?: JSX.Element;
  noCollapse?: boolean;
};

const ImageInput = ({
  onFilesSelected,
  selectDisabled,
  pendingImageNames,
  loadingProgress,
  helperText,
  rightPane,
  noCollapse,
}: ImageInputProps) => {
  const onDrop = useCallback(
    (acceptedFiles: any) => {
      onFilesSelected(acceptedFiles);
    },
    [onFilesSelected]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
  });

  const divClasses = classNames({
    dragActive: isDragActive,
    imageInputPromptContainer: true,
    imageLoading: selectDisabled,
  });

  const innerContent = (
    <Stack sx={{ width: "75%", alignSelf: "center" }} spacing={4}>
      <Paper {...getRootProps()} className={divClasses} elevation={2}>
        <input {...getInputProps()} />
        <FolderIcon className="imageInputIcon" color="primary" />
        <Typography
          variant="h5"
          align="center"
          sx={{ color: "hsl(291, 2%, 88%)" }}
        >
          {helperText || "Drag and drop images here."}
        </Typography>
      </Paper>
      {!noCollapse && (
        <Collapse in={pendingImageNames.length > 0} timeout={500}>
          <ImageProgressList
            pendingImageNames={pendingImageNames}
            curProgress={loadingProgress}
          />
        </Collapse>
      )}
    </Stack>
  );

  if (rightPane) {
    return <BaseView rightPane={rightPane}>{innerContent}</BaseView>;
  } else return innerContent;
};

export default ImageInput;
