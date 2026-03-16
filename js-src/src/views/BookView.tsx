import React, { useCallback, useState } from "react";
import BaseView from "./BaseView";
import { LinearProgress, Stack, Typography } from "@mui/material";
import {
  pollTranslateBookStatus,
  translateBook,
} from "../flaskcomms/bookViewComms";
import ImageInput from "./ImageView/components/ImageViewer/ImageInput";
import { useLoader } from "../components/LoaderContext";

const BookView = () => {
  const { loading, setLoading } = useLoader();

  const [loadingProgress, setLoadingProgress] = useState(0);
  const [sentsDone, setSentsDone] = useState(0);
  const [sentsTotal, setSentsTotal] = useState(0);

  const updateProgress = useCallback(
    (progress: number, sentencesDone: number, sentencesTotal: number) => {
      setLoadingProgress(Math.round(progress * 100));

      setSentsTotal(sentencesTotal);
      setSentsDone(sentencesDone);
    },
    []
  );

  const doneTranslating = useCallback(async () => {
    setLoading(false);
    setLoadingProgress(0);
    setSentsDone(0);
    setSentsTotal(0);
  }, []);

  const startTranslating = useCallback(() => {
    setLoadingProgress(0);
    setLoading(true);
  }, []);

  const handleSelectFiles = useCallback(
    async (files: any) => {
      if (!files || files.length === 0) return;

      startTranslating(); // Ensure the client is loading.
      await pollTranslateBookStatus(updateProgress, doneTranslating); // Create a websocket to listen to the server for progress and the end result.

      // Now we actually begin the translation job on the server.
      await translateBook(files[0], null);
    },
    [startTranslating, updateProgress, doneTranslating]
  );

  return (
    <BaseView>
      <ImageInput
        paperClassNames="bookInputPromptContainer"
        onFilesSelected={handleSelectFiles}
        selectDisabled={loading}
        loadingProgress={loadingProgress}
        pendingImageNames={[]}
        helperText={
          <Stack spacing={2}>
            Drag and drop an EPUB file here.
            {loading && (
              <Typography
                variant="body2"
                align="center"
                sx={{
                  color: "hsl(291, 3%, 74%)",
                  marginTop: "16px !important",
                }}
              >
                {sentsTotal > 0
                  ? `Translating... (${sentsDone} / ${sentsTotal})`
                  : "Translating..."}
              </Typography>
            )}
            {loading && (
              <LinearProgress variant="determinate" value={loadingProgress} />
            )}
          </Stack>
        }
      />
    </BaseView>
  );
};

export default BookView;
