import React from "react";
import { MenuItem, Paper, TextField, Typography } from "@mui/material";

// TODO: refactor with VideoViewOptions
export type BookProcessingModes = "none" | "html" | "epub";

export type BookViewOptionsProps = {
  mode: BookProcessingModes;
  setMode: (v: BookProcessingModes) => void;
};

const BookViewOptions = (props: BookViewOptionsProps) => {
  const selectMode = async (e: any) => {
    props.setMode(e.target.value);
  };

  return (
    <TextField
      select
      placeholder="Pick a mode..."
      onChange={selectMode}
      value={props.mode}
      fullWidth
      sx={{ boxShadow: 2, width: "75%" }}
      label="Mode"
      size="small"
    >
      <MenuItem value="epub">Epub</MenuItem>
      <MenuItem disabled value="" divider dense>
        <em
          style={{
            fontSize: "small",
            wordWrap: "break-word",
            whiteSpace: "initial",
          }}
        >
          The translated book will be saved as an EPUB file.
        </em>
      </MenuItem>
      <MenuItem value="html">HTML</MenuItem>
      <MenuItem disabled value="" divider dense>
        <em
          style={{
            fontSize: "small",
            wordWrap: "break-word",
            whiteSpace: "initial",
          }}
        >
          The translated book will be saved as an HTML file.
        </em>
      </MenuItem>
    </TextField>
  );
};

export default BookViewOptions;
