import React, { useEffect, useState, useCallback, memo } from "react";
import {
  Button,
  Collapse,
  Grid,
  Pagination,
  Stack,
  TextField,
  Typography,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import { useDropzone } from "react-dropzone";
import classNames from "classnames";
import ImageProgressList from "./ImageProgressList";
import AnnotatedImage from "./AnnotatedImage";
import ImageEditor from "../ImageEditor/ImageEditor";
import { MainGateway } from "../../../../utils/mainGateway";
import { useImageViewMode } from "../../../../components/ImageViewModeProvider";
import AmgViewerAnnotations from "./AmgViewerAnnotations";

const checkAmg = (fullPath: string) =>
  fullPath ? fullPath.endsWith(".amg") : false;

const getFontFamilies = () => {
  const families: string[] = [];

  document.fonts.forEach((v) => {
    families.push(v.family);
  });

  return [...new Set(families)];
};

export type ImageViewerProps = {
  imagePaths: string[];
  onFilesSelected: (d: any) => void;
  selectDisabled: boolean;
  loadingProgress: number;
  pendingImageNames: string[];
  onSaveEditedImage: (image: any, imagePath: string) => void;
  selectedPath: string | null; // Only used to change current index.
  canPageWithKeys: boolean;
};

// From: https://stackoverflow.com/questions/423376/how-to-get-the-file-name-from-a-full-path-using-javascript
const getFileName = (filePath: string) => {
  const s = filePath?.split("\\")?.pop()?.split("/")?.pop();
  if (!s) return s;

  if (s.length > 24) {
    return `${s.substring(0, 9)}...`;
  } else return s;
};

const ImageViewerNoMemo = ({
  imagePaths,
  onFilesSelected,
  selectDisabled,
  loadingProgress,
  pendingImageNames,
  onSaveEditedImage,
  selectedPath,
  canPageWithKeys,
}: ImageViewerProps) => {
  const theme = useTheme();
  const matchDownMd = useMediaQuery(theme.breakpoints.down("md"));

  const onDrop = useCallback(
    (acceptedFiles: any) => {
      onFilesSelected(acceptedFiles);
    },
    [onFilesSelected]
  );

  const { viewingMode, changeViewingMode } = useImageViewMode();

  const [curIndex, setCurIndex] = useState(0);

  const [curImage, setCurImage] = useState("");
  const [curAnnotations, setCurAnnotations] = useState<any[]>([]);
  const [isAmg, setIsAmg] = useState(false);

  const [originalWidth, setOriginalWidth] = useState(1);
  const [originalHeight, setOriginalHeight] = useState(1);

  const [isEditing, setIsEditing] = useState(false);

  const [fontFamilies, _setFontFamilies] = useState(getFontFamilies());

  const [pageFieldVal, setPageFieldVal] = useState("1");

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    noClick: true,
  });

  useEffect(() => {
    setCurIndex(0);
  }, [selectedPath]);

  useEffect(() => {
    const cb = (e: KeyboardEvent) => {
      if (!canPageWithKeys || isEditing) return;

      if (e.code === "ArrowLeft" || e.code == "KeyA") {
        // Left
        setCurIndex((c) => Math.max(0, c - 1));
      }

      if (e.code === "ArrowRight" || e.code == "KeyD") {
        // Right
        setCurIndex((c) => Math.min(imagePaths.length - 1, c + 1));
      }
    };

    document.addEventListener("keydown", cb);
    return () => {
      document.removeEventListener("keydown", cb);
    };
  }, [imagePaths.length, canPageWithKeys, isEditing]);

  const handlePageChange = (e: React.ChangeEvent<unknown>, page: number) => {
    // Arrays start at 0. Pages start at 1.

    setCurIndex(page - 1);
  };

  const handlePageFieldChange = (e: any) => {
    // Arrays start at 0. Pages start at 1.
    const { value } = e.currentTarget;
    const parsed = parseInt(value, 10);

    setPageFieldVal(value);

    if (Number.isNaN(parsed) || parsed - 1 < 0) return;
    if (parsed - 1 >= imagePaths.length) return;

    setCurIndex(parsed - 1);
  };

  useEffect(() => {
    if (curIndex !== null && curIndex !== undefined) {
      setPageFieldVal(`${curIndex + 1}`);
    }
  }, [curIndex]);

  useEffect(() => {
    let canceled = false;

    if (checkAmg(imagePaths[curIndex])) {
      const asyncCb = async () => {
        const amg = await MainGateway.openAMG(imagePaths[curIndex]);

        var i = new Image();

        i.onload = function () {
          if (canceled) return;

          setOriginalWidth(i.width);
          setOriginalHeight(i.height);
        };

        if (canceled) return;

        i.src = `data:image/jpeg;base64,${amg.image}`;

        setCurImage(amg.image);
        setCurAnnotations(amg.annotations); // AMG files have external annotations.
        setIsAmg(true);
        setIsEditing(false);

        changeViewingMode("one_amg"); // No library right pane. Instead, a separate AmgAnnotations panel is rendered instead.
      };

      asyncCb();
    } else {
      setCurImage(imagePaths[curIndex]); // Keep curImage as is - it already points to an image file.
      setCurAnnotations([]); // Images have no annotations - the translated text is instead already edited into the image itself.
      setIsAmg(false);
      setOriginalWidth(1);
      setOriginalHeight(1);
      setIsEditing(false);

      changeViewingMode("one");
    }

    return () => {
      canceled = true;
    };
  }, [curIndex, imagePaths, changeViewingMode]);

  const onSaveImage = useCallback(
    async (image: any) => {
      if (curIndex >= imagePaths.length) return;

      setIsEditing(false);
      await onSaveEditedImage(image, imagePaths[curIndex]);

      // TODO: Not super happy with these dependencies...
    },
    [imagePaths, curIndex, onSaveEditedImage]
  );

  const handleEditClick = () => {
    changeViewingMode("one");
    setIsEditing(true);
  };

  const imgClasses = classNames({
    dragActive: isDragActive,
    imagePreview: true,
    imageLoading: selectDisabled,
  });

  if (!imagePaths || imagePaths.length === 0)
    return <div data-testid="empty-viewer"></div>;

  // AMG files can be edited. ImageEditor has its own left pane.
  if (isAmg && isEditing) {
    return (
      <ImageEditor
        src={`data:image/jpeg;base64,${curImage}`}
        annotations={curAnnotations}
        originalImageHeight={originalHeight}
        originalImageWidth={originalWidth}
        fontFamilies={fontFamilies}
        onSaveImage={onSaveImage}
      />
    );
  } else {
    const progressComponent = (
      <Collapse
        in={pendingImageNames.length > 0}
        timeout={750}
        sx={{ marginBottom: 2 }}
        mountOnEnter
        unmountOnExit
      >
        <ImageProgressList
          pendingImageNames={pendingImageNames}
          curProgress={loadingProgress}
          dense
        />
      </Collapse>
    );

    const mainComponent = (withProgress: boolean) => (
      <>
        <div {...getRootProps()} className="imagePreviewRoot">
          {withProgress && progressComponent}
          <input {...getInputProps()} />
          <div
            className={
              viewingMode === "vertical"
                ? "imagePreviewContainerVertical"
                : "imagePreviewContainer"
            }
            style={{
              marginTop:
                pendingImageNames && pendingImageNames.length > 0
                  ? "2px"
                  : "-18px",
            }}
          >
            {viewingMode.startsWith("one") && (
              <div className="imagePreviewTitle">
                <Typography
                  variant="caption"
                  align="center"
                  sx={{ fontWeight: "500" }}
                >
                  {getFileName(imagePaths[curIndex])}
                </Typography>
              </div>
            )}
            {curIndex < imagePaths.length && viewingMode.startsWith("one") && (
              <AnnotatedImage
                annotations={curAnnotations}
                className={imgClasses}
                src={isAmg ? `data:image/jpeg;base64,${curImage}` : curImage}
                originalImageWidth={originalWidth}
                originalImageHeight={originalHeight}
                fitImage={true}
                onClick={() => {
                  if (isAmg) return; // AMG can't go vertical.

                  changeViewingMode();
                }}
              />
            )}
            {imagePaths.length > 0 &&
              !isAmg && // TODO: Add AMG support for vertical stuff. Though I doubt anyone will use it?
              viewingMode === "vertical" &&
              [...Array(imagePaths.length).keys()].map((_, idx) => (
                <AnnotatedImage
                  annotations={curAnnotations}
                  className={imgClasses}
                  src={
                    isAmg
                      ? `data:image/jpeg;base64,${imagePaths[idx]}`
                      : imagePaths[idx]
                  }
                  originalImageWidth={originalWidth}
                  originalImageHeight={originalHeight}
                  key={imagePaths[idx] || idx}
                  fitImage={false}
                  onClick={() => {
                    if (isAmg) return; // AMG can't go vertical.

                    changeViewingMode();
                  }}
                />
              ))}
            {isDragActive && (
              <Typography
                variant="h4"
                className="imageInputText"
                align="center"
              >
                Drop files here...
              </Typography>
            )}
          </div>
          {imagePaths.length > 1 && viewingMode.startsWith("one") && (
            <div className="imageViewerControls">
              <Pagination
                count={imagePaths.length}
                shape="rounded"
                onChange={handlePageChange}
                page={curIndex + 1}
                sx={{ marginBottom: "8px" }}
                className="imageViewerPagination"
                size={matchDownMd ? "small" : "medium"}
              />
              {!matchDownMd && (
                <TextField
                  type="number"
                  defaultValue={1}
                  value={pageFieldVal}
                  onChange={handlePageFieldChange}
                  className="imageViewerPageField"
                  InputLabelProps={{
                    shrink: true,
                  }}
                  sx={{ marginBottom: "8px" }}
                  variant="outlined"
                />
              )}
            </div>
          )}
          {isAmg && viewingMode.startsWith("one") && (
            <Stack spacing={2} direction="row" sx={{ marginBottom: "8px" }}>
              <Button
                variant="contained"
                sx={{
                  fontWeight: "normal",
                  color: "white !important",
                  backgroundColor: "primary.600",
                }}
                onClick={handleEditClick}
                fullWidth
              >
                Edit
              </Button>
            </Stack>
          )}
        </div>
      </>
    );

    if (viewingMode === "one_amg") {
      return (
        <Stack spacing={4}>
          {progressComponent}
          <Grid container spacing={1} sx={{ width: "60vw" }}>
            <Grid item xs={8} className="appContainerLeftNoHeight">
              {mainComponent(false)}
            </Grid>
            <Grid item xs={4} sx={{ display: "flex" }}>
              <AmgViewerAnnotations
                annotations={curAnnotations}
                selectedAnnotationId=""
              />
            </Grid>
          </Grid>
        </Stack>
      );
    } else return mainComponent(true);
  }
};

const ImageViewer = memo(ImageViewerNoMemo);

export default ImageViewer;
