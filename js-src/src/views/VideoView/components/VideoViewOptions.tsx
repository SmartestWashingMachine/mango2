import React, { useState, useEffect } from "react";
import { MenuItem, TextField } from "@mui/material";
import {
  asrModelInstalled,
  useInstalledModelsRetriever,
} from "../../../utils/useInstalledModelsRetriever";
import ErrorIcon from "@mui/icons-material/Error";
import ReportProblemIcon from "@mui/icons-material/ReportProblem";
import { checkFfmpegInstalled } from "../../../flaskcomms/videoViewComms";

export type VideoProcessingModes = "none" | "visual" | "audio";

export type VideoViewOptionsProps = {
  mode: VideoProcessingModes;
  setMode: (v: VideoProcessingModes) => void;
};

const VideoViewOptions = (props: VideoViewOptionsProps) => {
  const installedModels = useInstalledModelsRetriever();
  const [ffmpegInstalled, setFfmpegInstalled] = useState(false);

  useEffect(() => {
    let canceled = false;

    const cb = async () => {
      const data = await checkFfmpegInstalled();

      if (!canceled) setFfmpegInstalled(data?.installed);
    };

    cb();

    return () => {
      canceled = true;
    };
  }, []);

  const selectMode = async (e: any) => {
    props.setMode(e.target.value);
  };

  const ffmpegError = (
    <MenuItem disabled value="" divider dense>
      <em
        style={{
          fontSize: "small",
          wordWrap: "break-word",
          whiteSpace: "initial",
          color: "#d32f2f",
          fontWeight: "500",
          fontStyle: "normal",
          display: "flex",
          alignItems: "center",
          gap: "4px",
        }}
      >
        <ErrorIcon style={{ fontSize: "1rem" }} />
        Please install FFMPEG and FFProbe.
      </em>
    </MenuItem>
  );

  const asrWarning = (
    <MenuItem disabled value="" divider dense>
      <em
        style={{
          fontSize: "small",
          wordWrap: "break-word",
          whiteSpace: "initial",
          color: "#ed6c02",
          fontWeight: "500",
          fontStyle: "normal",
          display: "flex",
          alignItems: "center",
          gap: "4px",
        }}
      >
        <ReportProblemIcon style={{ fontSize: "1rem" }} />
        Please install the ASR model to use this feature.
      </em>
    </MenuItem>
  );

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
      {!ffmpegInstalled && ffmpegError}
      <MenuItem value="visual" disabled={!ffmpegInstalled}>
        Visual
      </MenuItem>
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
      <MenuItem
        value="audio"
        disabled={!ffmpegInstalled || !asrModelInstalled(installedModels)}
      >
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
      {ffmpegInstalled && !asrModelInstalled(installedModels) && asrWarning}
    </TextField>
  );
};

export default VideoViewOptions;
