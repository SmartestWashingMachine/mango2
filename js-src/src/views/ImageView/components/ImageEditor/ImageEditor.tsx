import { Box, Button, Grid, Stack, Typography } from "@mui/material";
import React, { useEffect, useRef, useState } from "react";
import IAnnotation, { IAnnotationStyles } from "../../../../types/Annotation";
import ImageEditorItem from "./ImageEditorItem";
import ImageEditorOptions from "./ImageEditorOptions";
import { v4 } from "uuid";
import { useResizeDetector } from "react-resize-detector";
import { MainGateway } from "../../../../utils/mainGateway";

// @ts-ignore
import domtoimage from "dom-to-image-more";
import ITextPreset from "../../../../types/TextPreset";
import PresetSelector from "./PresetSelector";

// TODO: Add tests

const getDefaultAnnotationStyles = (fontFamilies: any[]) => {
  const output: IAnnotationStyles = {
    isItalic: false,
    isBold: false,
    textAlign: "center",
    fontSize: 16,
    fontFamily: fontFamilies[0],
    strokeSize: 0,
    strokeColor: "#000000",
    fontColor: "#000000",
    hasBackgroundColor: true,
    backgroundColor: "#FFFFFF",
    borderRadius: 0,
    verticalCenter: true,
  };

  return output;
};

// As of the time I'm writing this comment, I haven't even started writing the image editor and I already know it promises nothing but pain.
// As of the time I'm writing this comment, I just got the image editor to a basic working state and I already hate it.

export type ImageEditorProps = {
  src: string;
  annotations: IAnnotation[];
  className?: string;
  originalImageWidth: number;
  originalImageHeight: number;
  fontFamilies: string[];
  onSaveImage: (imageBlob: any) => void;
};

const ImageEditor = ({
  src,
  annotations,
  className,
  originalImageWidth,
  originalImageHeight,
  fontFamilies,
  onSaveImage,
}: ImageEditorProps) => {
  const [localAnnotations, setLocalAnnotations] = useState<IAnnotation[]>([]);
  const [selectedIdx, setSelectedIdx] = useState(0);

  const {
    width: containerWidth,
    height: containerHeight,
    ref,
  } = useResizeDetector();

  const [isProcessing, setIsProcessing] = useState(false);

  const [presets, setPresets] = useState<ITextPreset[]>([]);

  useEffect(() => {
    // Annotations prop isn't actually IAnnotation. It's a basic annotation object only containing the text and position properties.
    const defaultStyles: Partial<IAnnotation> = {
      ...getDefaultAnnotationStyles(fontFamilies),
    };

    const mapped = annotations.map((a) => ({
      ...a,
      ...defaultStyles,
      uuid: v4(),
    }));

    setLocalAnnotations(mapped);
  }, [annotations]);

  const changeAnnotation = (
    annoId: string,
    key: keyof IAnnotation | null,
    value: any,
    isObj = false
  ) => {
    let newAnnotations: IAnnotation[] = [];
    if (isObj) {
      // If using isObj, "key" is ignored, and "value" should be a partial annotation object.
      newAnnotations = localAnnotations.map((a, i) =>
        selectedIdx === i ? { ...a, ...value } : a
      );
    } else if (key) {
      newAnnotations = localAnnotations.map((a, i) =>
        selectedIdx === i ? { ...a, [key]: value } : a
      );
    } else
      throw Error(
        'For changeAnnotation, key can only be "null" if using isObj. (isObj is used to set multiple fields)'
      );

    setLocalAnnotations(newAnnotations);
  };

  const deleteAnnotation = (annoId: string) => {
    const newAnnotations = localAnnotations.filter((a, i) => selectedIdx !== i);
    setLocalAnnotations(newAnnotations);

    setSelectedIdx((s) => s - 1);
  };

  const createAnnotation = () => {
    setSelectedIdx(localAnnotations.length);

    const newAnnotation: IAnnotation = {
      text: "Text",
      // TODO: Better position defaults.
      x1: 25,
      y1: 25,
      x2: 150,
      y2: 150,
      ...getDefaultAnnotationStyles(fontFamilies),
      uuid: v4(), // used for keys in html.
    };

    setLocalAnnotations((a) => [...a, newAnnotation]);
  };

  const saveImage = async () => {
    setIsProcessing(true);
  };

  useEffect(() => {
    if (isProcessing) {
      let didCancel = false;

      const asyncCb = async () => {
        if (didCancel) return;

        const element = document.getElementById("image-preview-box");
        if (!element) return;

        const scale = Math.min(
          element.offsetWidth / originalImageWidth,
          element.offsetHeight / originalImageHeight
        );

        const nodeStyles = {
          height: element.offsetHeight * scale,
          width: element.offsetWidth * scale,
          quality: 1,
          style: {
            transform: "scale(" + scale + ")",
            transformOrigin: "top left",
            width: element.offsetWidth + "px",
            height: element.offsetHeight + "px",
          },
        };

        const dataUrl = await domtoimage.toPng(element, nodeStyles);

        // See: https://stackoverflow.com/questions/55987650/how-can-i-save-imagedata-as-a-png-in-electron
        const output = dataUrl.substring("data:image/png;base64,".length);

        if (!didCancel) {
          setIsProcessing(false);
          onSaveImage(output);
        }

        return;
      };

      setTimeout(() => {
        asyncCb();
      }, 3000);

      return () => {
        didCancel = true;
      };
    }
  }, [isProcessing, onSaveImage]);

  const handleSelect = (idx: number) => {
    setSelectedIdx(idx);
  };

  const savePreset = async (p: ITextPreset) => {
    const newPresets = [...presets, p];
    setPresets(newPresets);

    await MainGateway.setStoreValue("presets", newPresets);
  };

  const deletePreset = async (presetUuid: string) => {
    const filtered = presets.filter((otherP) => otherP.uuid !== presetUuid);

    await MainGateway.setStoreValue("presets", filtered);

    setPresets(filtered);
  };

  useEffect(() => {
    // Fetch presets once at load.

    let didCancel = false;

    const asyncCb = async () => {
      const data = await MainGateway.getStoreData();

      if (!didCancel) {
        setPresets(data?.presets);
      }
    };

    asyncCb();

    return () => {
      didCancel = true;
    };
  }, []);

  const selectGlobalPreset = (e: any) => {
    const foundPreset = presets.find((p) => p.uuid === e.target.value);
    if (!foundPreset) return;

    // Set the styles for ALL present annotations.
    const newAnnotations = localAnnotations.map((a) => ({
      ...a,
      ...foundPreset.annotationStyles,
    }));
    setLocalAnnotations(newAnnotations);
  };

  const [canDrag, setCanDrag] = useState(false);

  useEffect(() => {
    // Add a keybind to toggle drag/resize mode.

    const keyDownHandler = (e: KeyboardEvent) => {
      if (e.key === "Shift") setCanDrag(true);
    };
    const keyUpHandler = (e: KeyboardEvent) => {
      if (e.key === "Shift") setCanDrag(false);
    };

    window.addEventListener("keydown", keyDownHandler);
    window.addEventListener("keyup", keyUpHandler);

    return () => {
      window.removeEventListener("keydown", keyDownHandler);
      window.removeEventListener("keyup", keyUpHandler);
    };
  }, []);

  const leftPane = (
    <Stack spacing={2}>
      {selectedIdx < localAnnotations.length && selectedIdx >= 0 && (
        <ImageEditorOptions
          fontFamilies={fontFamilies}
          a={localAnnotations[selectedIdx]}
          onDeleteAnnotation={deleteAnnotation}
          onChangeProperty={changeAnnotation}
          presets={presets}
          onSavePreset={savePreset}
          onDeletePreset={deletePreset}
        />
      )}
      <PresetSelector
        selectPreset={selectGlobalPreset}
        deletePreset={deletePreset}
        presets={presets}
        buttonText="Use Preset Globally"
        color="secondary"
      />
      <Button variant="outlined" onClick={createAnnotation}>
        New Text
      </Button>
      <Button variant="contained" color="secondary" onClick={saveImage}>
        Save Image
      </Button>
      <Stack spacing={1}>
        <Typography variant="caption" sx={{ color: "hsl(291, 3%, 74%)" }}>
          Click on a text field to select it.
        </Typography>
        <Typography variant="caption" sx={{ color: "hsl(291, 3%, 74%)" }}>
          Hold "SHIFT" and move the field using the mouse.
        </Typography>
        <Typography variant="caption" sx={{ color: "hsl(291, 3%, 74%)" }}>
          Drag the bottom right edge to resize it.
        </Typography>
        <Typography variant="caption" sx={{ color: "hsl(291, 3%, 74%)" }}>
          Drag the top left edge to rotate the text inside.
        </Typography>
      </Stack>
    </Stack>
  );

  // imagePreviewProcessing is actually an empty class lol - we just wanna remove the max-width & max-height properties while processing.
  return (
    <Grid container spacing={2}>
      <Box
        component={Grid}
        display={{ xs: "none", sm: "none", md: "grid" }}
        item
        xs={0}
        sm={0}
        md={3}
      >
        {leftPane}
      </Box>
      <Box
        item
        xs={12}
        sm={12}
        md={0}
        component={Grid}
        display={{ xs: "grid", sm: "grid", md: "none" }}
        sx={{ alignItems: "center" }}
      >
        <Typography color="primary" align="center" variant="h4">
          Please make the app full screen...
        </Typography>
      </Box>
      <Box
        component={Grid}
        display={{
          xs: "none",
          sm: "none",
          md: "grid",
          justifyContent: "center",
          alignContent: "center",
        }}
        item
        className="imagePreviewContainer"
        xs={0}
        sm={0}
        md={9}
      >
        <div
          className={
            isProcessing ? "imageEditorBoxProcessing" : "imageEditorBox"
          }
          id="image-preview-box"
          data-testid="image-preview-box"
        >
          <img
            src={src}
            className={
              isProcessing ? "editImagePreviewProcessing" : "editImagePreview"
            }
            ref={ref}
          />
          {localAnnotations.map((a, idx) => (
            <ImageEditorItem
              originalImageHeight={originalImageHeight}
              originalImageWidth={originalImageWidth}
              a={a}
              key={a.uuid}
              containerWidth={containerWidth || 0}
              containerHeight={containerHeight || 0}
              onSelect={() => handleSelect(idx)}
              canDrag={canDrag}
            />
          ))}
        </div>
      </Box>
    </Grid>
  );
};

export default ImageEditor;
