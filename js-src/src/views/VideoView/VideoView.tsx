import React, { useCallback, useState } from "react";
import BaseView from "../BaseView";
import { LinearProgress, Stack, Typography } from "@mui/material";
import {
  pollTranslateVideoStatus,
  translateVideo,
} from "../../flaskcomms/videoViewComms";
import ImageInput from "../ImageView/components/ImageViewer/ImageInput";
import { useLoader } from "../../components/LoaderContext";
import { useAlerts } from "../../components/AlertProvider";
import VideoViewOptions, {
  VideoProcessingModes,
} from "./components/VideoViewOptions";

const VideoView = () => {
  const pushAlert = useAlerts();
  const { loading, setLoading } = useLoader();

  const [loadingProgress, setLoadingProgress] = useState(0);

  const [mode, setMode] = useState<VideoProcessingModes>("none");

  const updateProgress = useCallback((progress: number) => {
    setLoadingProgress(Math.round(progress * 100));
  }, []);

  const doneTranslating = useCallback(
    async (outPath: string) => {
      setLoading(false);
      setLoadingProgress(0);

      pushAlert(`Video saved in: "${outPath}"`);
    },
    [pushAlert]
  );

  const startTranslating = useCallback(() => {
    setLoadingProgress(0);
    setLoading(true);
  }, []);

  const handleSelectFiles = useCallback(
    async (files: any) => {
      if (!files || files.length === 0) return;

      startTranslating(); // Ensure the client is loading.
      await pollTranslateVideoStatus(updateProgress, doneTranslating); // Create a websocket to listen to the server for progress and the end result.

      // Now we actually begin the translation job on the server.
      // See: https://github.com/electron/electron/blob/v1.2.8/docs/api/file-object.md
      await translateVideo(files[0].path, mode);
    },
    [startTranslating, updateProgress, doneTranslating]
  );

  const modeHelperText =
    mode === "none"
      ? "Pick a mode above first..."
      : "Drag and drop an MP4 file here.";

  return (
    <BaseView>
      <Stack spacing={2} sx={{ alignItems: "center" }}>
        <VideoViewOptions mode={mode} setMode={setMode} />
        <ImageInput
          paperClassNames="videoInputPromptContainer"
          onFilesSelected={handleSelectFiles}
          selectDisabled={loading || mode === "none"}
          loadingProgress={loadingProgress}
          pendingImageNames={[]}
          helperText={
            <Stack spacing={2}>
              {modeHelperText}
              <Typography
                variant="caption"
                align="center"
                sx={{ color: "hsl(291, 3%, 74%)" }}
                gutterBottom={false}
              >
                FFMPEG and FFProbe must be installed and in the system path. The
                video must NOT have any non alphabetic characters in the name
                and path.
              </Typography>
              {loading && (
                <LinearProgress
                  color="primary"
                  variant="determinate"
                  value={loadingProgress + 35}
                />
              )}
            </Stack>
          }
          noCollapse
        />
      </Stack>
    </BaseView>
  );
};

export default VideoView;
