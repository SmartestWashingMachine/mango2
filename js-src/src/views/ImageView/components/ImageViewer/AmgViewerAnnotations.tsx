import {
  Box,
  Card,
  CardActionArea,
  CardContent,
  Divider,
  Paper,
  Stack,
  Typography,
} from "@mui/material";
import React, { useEffect, useState, useCallback, useRef } from "react";
import IAnnotation, { IAnnotationStyles } from "../../../../types/Annotation";
import { useImageViewMode } from "../../../../components/ImageViewModeProvider";
import { getColorForIndex } from "./getColorForIndex";

// Get all elements in the array after and including the first element that matches the predicate.
// Returns the whole array if no match is found.
const arrSliceWhere = <T extends any>(arr: T[], cond: (item: T) => boolean) => {
  const idx = arr.findIndex(cond);
  if (idx === -1) return arr;

  return arr.slice(idx);
};

export type AmgViewerAnnotationsProps = {
  annotations: IAnnotation[];
  selectedAnnotationId: string;
};

const AmgViewerAnnotations = (props: AmgViewerAnnotationsProps) => {
  const scrollRef = useRef<any>(null);

  const {
    viewingAnnotationIdx,
    setViewingAnnotationTextIdx,
    setViewingAnnotationIdx,
    viewingAnnotationTextIdx,
  } = useImageViewMode();

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.focus();
      scrollRef.current.scrollTop = 0;

      setViewingAnnotationTextIdx(0);
      setViewingAnnotationIdx(0);
    }
  }, [props.annotations]);

  return (
    <Paper
      sx={{
        width: "100%",
        height: "85vh",
        overflowY: "auto",
        overflowX: "hidden",
        outline: "none",
        overflowWrap: "break-word",
      }}
      tabIndex={0}
      ref={scrollRef}
    >
      <Stack spacing={0}>
        <Typography
          variant="body2"
          sx={{
            width: "100%",
            backgroundColor: "hsl(291, 12%, 11%)",
            padding: "12px",
            paddingLeft: "16px",
          }}
        >
          Translations
        </Typography>
        {props.annotations.slice(viewingAnnotationIdx).map((x, idx) => (
          <Box
            key={`${x.text}-${x.x1}-${x.x2}-${x.y1}-${x.y2}`}
            onMouseEnter={() => {
              setViewingAnnotationTextIdx(viewingAnnotationIdx + idx);
            }}
            onMouseLeave={() => {
              setViewingAnnotationTextIdx(0);
            }}
          >
            <Stack spacing={1} direction="row">
              <Box
                sx={{
                  p: 2,
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "center",
                }}
              >
                <Typography
                  variant="caption"
                  sx={{ color: getColorForIndex(viewingAnnotationIdx + idx) }}
                >
                  {viewingAnnotationIdx + idx + 1}
                </Typography>
              </Box>
              <Box
                sx={{
                  p: 2,
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "center",
                }}
              >
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{
                    fontWeight:
                      (idx === 0 && viewingAnnotationTextIdx === 0) ||
                      viewingAnnotationTextIdx === idx
                        ? "500"
                        : "normal",
                  }}
                >
                  {x.text}
                </Typography>
                <Typography
                  variant="body2"
                  color="text.secondary"
                  mt="2px"
                  fontSize="0.6rem"
                  sx={{
                    opacity: 0.75,
                    fontWeight:
                      (idx === 0 && viewingAnnotationTextIdx === 0) ||
                      viewingAnnotationTextIdx === idx
                        ? "500"
                        : "normal",
                  }}
                >
                  {x.sourceText}
                </Typography>
              </Box>
            </Stack>
            <Divider sx={{ width: "90%" }} />
          </Box>
        ))}
      </Stack>
    </Paper>
  );
};

export default AmgViewerAnnotations;
