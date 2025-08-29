import {
  Button,
  Dialog,
  DialogActions,
  DialogContentText,
  DialogTitle,
  MenuItem,
  Stack,
  TextField,
} from "@mui/material";
import React, { useEffect, useRef } from "react";

type CreateNameFromItemDialogProps = {
  onDone: () => void;
  open: boolean;
  onClose: () => void;
  source: string;
  target: string;
  gender: string;
  setTarget: (t: string) => void;
  setGender: (g: string) => void;
};

const CreateNameFromItemDialog = (props: CreateNameFromItemDialogProps) => {
  const ref = useRef<any>(null);

  useEffect(() => {
    ref.current?.focus();
  }, [open]);

  const onTargetChange = (e: any) => {
    props.setTarget(e.currentTarget.value);
  };

  const handleDone = () => {
    props.onDone();
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleDone();
    }
  };

  return (
    <Dialog open={props.open} onClose={props.onClose}>
      <DialogTitle>Add Name To Dictionary</DialogTitle>
      <DialogContentText style={{ marginBottom: 16, padding: "0 24px" }}>
        This name was automatically detected by the name module. Specify what
        the translation should be. The translation model will prioritize using
        this translation when possible.
      </DialogContentText>
      <Stack
        spacing={2}
        sx={{
          paddingLeft: 4,
          paddingRight: 4,
          marginBottom: 1,
          marginTop: 1,
        }}
      >
        <TextField
          autoFocus
          margin="dense"
          value={props.source}
          fullWidth
          variant="standard"
          onKeyDown={onKeyDown}
          label="Detected Name"
          disabled // Can't edit source name.
        />
        <TextField
          autoFocus
          margin="dense"
          onChange={onTargetChange}
          value={props.target}
          fullWidth
          variant="standard"
          inputRef={ref} // To give auto-focus.
          onKeyDown={onKeyDown}
          label="Translated Name"
        />
        <TextField
          select
          margin="dense"
          fullWidth
          label="Gender"
          variant="standard"
          onChange={(e) => props.setGender(e.target.value)}
          value={props.gender}
        >
          <MenuItem value="">N/A</MenuItem>
          <MenuItem value="Male">Male</MenuItem>
          <MenuItem value="Female">Female</MenuItem>
        </TextField>
      </Stack>
      <DialogActions>
        <Button
          onClick={handleDone}
          fullWidth
          disabled={props.target.length === 0}
        >
          Add
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CreateNameFromItemDialog;
