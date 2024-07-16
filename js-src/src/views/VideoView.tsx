import React, { useCallback, useState } from "react";
import BaseView from "./BaseView";
import { Stack, Typography } from "@mui/material";
import {
  pollTranslateVideoStatus,
  translateVideo,
} from "../flaskcomms/videoViewComms";
import ImageInput from "./ImageView/components/ImageViewer/ImageInput";
import { useLoader } from "../components/LoaderContext";
import { useAlerts } from "../components/AlertProvider";

const VideoView = () => {
  const pushAlert = useAlerts();
  const { loading, setLoading } = useLoader();

  const [loadingProgress, setLoadingProgress] = useState(0);

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
      await translateVideo(files[0].path);
    },
    [startTranslating, updateProgress, doneTranslating]
  );

  return (
    <BaseView>
      <ImageInput
        onFilesSelected={handleSelectFiles}
        selectDisabled={loading}
        loadingProgress={loadingProgress}
        pendingImageNames={[]}
        helperText={"Drag and drop an MP4 file here."}
        noCollapse
      />
      <Stack spacing={1}>
        <Stack spacing={2}>
          <Typography
            variant="body2"
            align="center"
            sx={{ color: "hsl(291, 3%, 74%)" }}
            gutterBottom={false}
          >
            The AI will detect written text (NOT audio) in the video and create
            English subtitles for them.
          </Typography>
          <Typography
            variant="caption"
            align="center"
            sx={{ color: "hsl(291, 3%, 74%)" }}
            gutterBottom={false}
          >
            FFMPEG and FFProbe are required and must be added into the path. The video must NOT have any non alphabetic characters in the name and path.
          </Typography>
        </Stack>
        {loading && (
          <Typography variant="h5" align="center" sx={{ color: "#ba68c8" }}>
            {loadingProgress}%
          </Typography>
        )}
      </Stack>
    </BaseView>
  );
};

export default VideoView;

//^ side view perhaps ?
