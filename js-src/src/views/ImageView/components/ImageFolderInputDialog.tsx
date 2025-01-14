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

type ImageFolderInputDialogProps = {
  onDone: (folderName: string) => void;
  open: boolean;
  rootItem: FileInfo | null;
  onClose: () => void;
};

const ImageFolderInputDialog = (props: ImageFolderInputDialogProps) => {
  const [folderName, setFolderName] = useState("");
  const ref = useRef<any>(null);

  useEffect(() => {
    setFolderName("");
    ref.current?.focus();
  }, [open]);

  const onChange = (e: any) => setFolderName(e.currentTarget.value);

  const badFolderName =
    !isValidFilename(folderName) && folderName.trim().length > 0;

  const handleDone = () => {
    // Existing folders can still be used - it's just a warning.
    if (badFolderName || folderName.trim().length === 0) return;

    props.onDone(folderName.trim());
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
        style={{ padding: "0 24px", marginBottom: 12 }}
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
      <DialogActions>
        <Button onClick={handleDone} fullWidth disabled={badFolderName}>
          Done
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ImageFolderInputDialog;
