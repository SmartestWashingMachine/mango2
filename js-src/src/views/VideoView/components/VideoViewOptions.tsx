import React from "react";
import { MenuItem, Paper, TextField, Typography } from "@mui/material";
import {
  asrModelInstalled,
  useInstalledModelsRetriever,
} from "../../../utils/useInstalledModelsRetriever";
import { useState } from "react";

export type VideoProcessingModes = "none" | "visual" | "audio";

export type VideoViewOptionsProps = {
  mode: VideoProcessingModes;
  setMode: (v: VideoProcessingModes) => void;
};

const VideoViewOptions = (props: VideoViewOptionsProps) => {
  const installedModels = useInstalledModelsRetriever();

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
      <MenuItem value="visual">Visual</MenuItem>
      <MenuItem disabled value="" divider dense>
        <em
          style={{
            fontSize: "small",
            wordWrap: "break-word",
            whiteSpace: "initial",
          }}
        >
          Detect written text (NOT audio) in the video and create English
          subtitles.
        </em>
      </MenuItem>
      <MenuItem value="audio" disabled={!asrModelInstalled(installedModels)}>
        Audio
      </MenuItem>
      <MenuItem disabled value="" divider dense>
        <em
          style={{
            fontSize: "small",
            wordWrap: "break-word",
            whiteSpace: "initial",
          }}
        >
          Detect speech audio in the video and create English subtitles.
        </em>
      </MenuItem>
    </TextField>
  );
};

export default VideoViewOptions;
