import React, { useEffect, useState, useCallback } from "react";
import {
  Button,
  Collapse,
  Pagination,
  TextField,
  Typography,
} from "@mui/material";
import { useDropzone } from "react-dropzone";
import classNames from "classnames";
import ImageProgressList from "./ImageProgressList";
import AnnotatedImage from "./AnnotatedImage";
import ImageEditor from "../ImageEditor/ImageEditor";
import { MainGateway } from "../../../../utils/mainGateway";
import { useImageViewMode } from "../../../../components/ImageViewModeProvider";

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

const ImageViewer = ({
  imagePaths,
  onFilesSelected,
  selectDisabled,
  loadingProgress,
  pendingImageNames,
  onSaveEditedImage,
  selectedPath,
  canPageWithKeys,
}: ImageViewerProps) => {
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
      if (!canPageWithKeys) return;

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
  }, [imagePaths.length, canPageWithKeys]);

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
      };

      asyncCb();
    } else {
      setCurImage(imagePaths[curIndex]); // Keep curImage as is - it already points to an image file.
      setCurAnnotations([]); // Images have no annotations - the translated text is instead already edited into the image itself.
      setIsAmg(false);
      setOriginalWidth(1);
      setOriginalHeight(1);
      setIsEditing(false);
    }

    return () => {
      canceled = true;
    };
  }, [curIndex, imagePaths]);

  const onSaveImage = useCallback(
    async (image: any) => {
      if (curIndex >= imagePaths.length) return;

      setIsEditing(false);
      await onSaveEditedImage(image, imagePaths[curIndex]);

      // TODO: Not super happy with these dependencies...
    },
    [imagePaths, curIndex, onSaveEditedImage]
  );

  const handleEditClick = () => setIsEditing(true);

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
  } else
    return (
      <div {...getRootProps()} className="imagePreviewRoot">
        <Collapse
          in={pendingImageNames.length > 0}
          timeout={750}
          sx={{ marginBottom: 2 }}
        >
          <ImageProgressList
            pendingImageNames={pendingImageNames}
            curProgress={loadingProgress}
            dense
          />
        </Collapse>
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
          {viewingMode === "one" && (
            <div className="imagePreviewTitle">
              <Typography variant="h6" align="center">
                {getFileName(imagePaths[curIndex])}
              </Typography>
            </div>
          )}
          {curIndex < imagePaths.length && viewingMode === "one" && (
            <AnnotatedImage
              annotations={curAnnotations}
              className={imgClasses}
              src={isAmg ? `data:image/jpeg;base64,${curImage}` : curImage}
              originalImageWidth={originalWidth}
              originalImageHeight={originalHeight}
              fitImage={true}
              onClick={changeViewingMode}
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
                onClick={changeViewingMode}
              />
            ))}
          {isDragActive && (
            <Typography variant="h4" className="imageInputText" align="center">
              Drop files here...
            </Typography>
          )}
        </div>
        {imagePaths.length > 1 && viewingMode === "one" && (
          <div className="imageViewerControls">
            <Pagination
              count={imagePaths.length}
              shape="rounded"
              onChange={handlePageChange}
              page={curIndex + 1}
              sx={{ marginBottom: "8px" }}
              className="imageViewerPagination"
            />
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
          </div>
        )}
        {isAmg && viewingMode === "one" && (
          <Button
            variant="text"
            color="primary"
            onClick={handleEditClick}
            sx={{ marginBottom: "8px" }}
          >
            Edit
          </Button>
        )}
      </div>
    );
};

export default ImageViewer;
