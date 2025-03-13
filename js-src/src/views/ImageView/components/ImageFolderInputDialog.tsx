import {
  Button,
  Dialog,
  DialogActions,
  DialogContentText,
  DialogTitle,
  TextField,
  Tooltip,
} from "@mui/material";
import React, { useEffect, useState, useCallback, useRef } from "react";
import isValidFilename from "valid-filename";
import FileInfo from "../../../types/FileInfo";
import UpdateCheckbox from "../../../components/UpdateCheckbox";

type ImageFolderInputDialogProps = {
  onDone: (folderName: string, processFilesByModDate: boolean) => void;
  open: boolean;
  rootItem: FileInfo | null;
  onClose: () => void;
  folderName: string | null;
  setFolderName: (s: string) => void;
  processFilesByModifiedDate: boolean;
  setProcessFilesByModifiedDate: (b: boolean) => void;
};

const ImageFolderInputDialog = (props: ImageFolderInputDialogProps) => {
  let {
    folderName,
    setFolderName,
    processFilesByModifiedDate,
    setProcessFilesByModifiedDate,
  } = props;
  folderName = folderName || "";

  const ref = useRef<any>(null);

  useEffect(() => {
    // setFolderName("");
    ref.current?.focus();
  }, [open]);

  const onChange = (e: any) => {
    props.setFolderName(e.currentTarget.value);
  };

  const badFolderName =
    !isValidFilename(folderName) && folderName.trim().length > 0;

  const handleDone = () => {
    // Existing folders can still be used - it's just a warning.
    if (badFolderName || folderName.trim().length === 0) return;

    props.onDone(folderName.trim(), processFilesByModifiedDate);
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleDone();
    }
  };

  // Only goes to depth 1.
  const folderExists =
    !!props.rootItem &&
    !!props.rootItem.childrenItems.find(
      (c) => c.fileName.toLowerCase() === folderName.toLowerCase().trim()
    );

  let errorMessage = " ";
  if (badFolderName) errorMessage = "Invalid file name.";
  if (folderExists) errorMessage = "This folder already exists.";

  return (
    <Dialog open={props.open} onClose={props.onClose}>
      <DialogTitle>Folder Name</DialogTitle>
      <DialogContentText style={{ marginBottom: 16, padding: "0 24px" }}>
        The selected images will be translated and placed in the folder.
      </DialogContentText>
      <TextField
        autoFocus
        style={{ padding: "0 24px" }}
        placeholder="Folder"
        onChange={onChange}
        value={folderName}
        fullWidth
        variant="standard"
        inputRef={ref}
        error={badFolderName}
        helperText={errorMessage}
        onKeyDown={onKeyDown}
        color={folderExists ? "warning" : undefined}
      />
      <UpdateCheckbox
        changeValue={(_, v) => setProcessFilesByModifiedDate(v)}
        keyName="n/a"
        defaultValue={processFilesByModifiedDate}
        label="Process Files by Date"
        // helperText="Disable this if you want to process files in the order of their names."
        style={{ padding: "0 21px", marginBottom: 12 }}
      />
      <DialogActions>
        <Button onClick={handleDone} fullWidth disabled={badFolderName}>
          Done
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ImageFolderInputDialog;
