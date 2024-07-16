import React, { useState } from "react";
import {
  Button,
  Checkbox,
  Collapse,
  Fade,
  FormControl,
  FormControlLabel,
  IconButton,
  InputAdornment,
  InputLabel,
  ListItem,
  Menu,
  MenuItem,
  Paper,
  Select,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import IAnnotation, { IAnnotationStyles } from "../../../../types/Annotation";
import { HexColorPicker } from "react-colorful";
import ITextPreset from "../../../../types/TextPreset";
import { v4 as uuidv4 } from "uuid";
import ArrowCircleRightIcon from "@mui/icons-material/ArrowRight";
import PresetSelector from "./PresetSelector";
import ImageEditorSubtitle from "./ImageEditorSubtitle";

export type ImageEditorOptionsProps = {
  a: IAnnotation;
  fontFamilies: string[]; // List of allowed font families.
  presets: ITextPreset[];
  onDeleteAnnotation: (annoId: string) => void;
  onChangeProperty: (
    annoId: string,
    key: keyof IAnnotation | null,
    value: any,
    isObj: boolean
  ) => void;
  onSavePreset: (preset: ITextPreset) => void;
  onDeletePreset: (uuid: string) => void;
};

// Options for one text item in the image editor.
const ImageEditorOptions = (props: ImageEditorOptionsProps) => {
  const { a } = props;

  const changeProperty = (key: keyof IAnnotation, value: any) => {
    props.onChangeProperty(a.uuid, key, value, false);
  };

  const updateFontFamily = (e: any) => {
    changeProperty("fontFamily", e.target.value);
  };

  const updateTextAlign = (e: any) => {
    changeProperty("textAlign", e.target.value);
  };

  const updateFontSize = (e: any) => {
    changeProperty("fontSize", e.currentTarget.value);
  };

  const handleDeleteAnnotation = () => {
    props.onDeleteAnnotation(props.a.uuid);
  };

  const updateStrokeSize = (e: any) => {
    changeProperty("strokeSize", e.currentTarget.value);
  };

  const updateBold = (e: any) => {
    changeProperty("isBold", e.currentTarget.checked);
  };

  const updateItalic = (e: any) => {
    changeProperty("isItalic", e.currentTarget.checked);
  };

  const updateStrokeColor = (e: any) => {
    changeProperty("strokeColor", e);
  };

  const updateFontColor = (e: any) => {
    changeProperty("fontColor", e);
  };

  const updateHasBackgroundColor = (e: any) => {
    changeProperty("hasBackgroundColor", e.currentTarget.checked);
  };

  const updateBackgroundColor = (e: any) => {
    changeProperty("backgroundColor", e);
  };

  const updateBorderRadius = (e: any) => {
    changeProperty("borderRadius", e.currentTarget.value);
  };

  const updateVerticalCenter = (e: any) => {
    changeProperty("verticalCenter", e.currentTarget.checked);
  };

  const selectPreset = (e: any) => {
    const foundPreset = props.presets.find((p) => p.uuid === e.target.value);
    if (!foundPreset) return;

    // Set style values to those in the preset.
    // We call onChangeProperty as we can change multiple values at once.
    props.onChangeProperty(a.uuid, null, foundPreset.annotationStyles, true);
  };

  const [newPresetName, setNewPresetName] = useState("");

  const savePreset = () => {
    const nonStyleNames: (keyof IAnnotation)[] = [
      "text",
      "uuid",
      "x1",
      "x2",
      "y1",
      "y2",
    ];

    // Only add proper styles (not text property, uuid property, etc...)
    const aStyles: any = {};
    for (const k in a) {
      if (nonStyleNames.indexOf(k as keyof IAnnotation) === -1)
        aStyles[k] = a[k as keyof IAnnotation];
    }

    const newPreset: ITextPreset = {
      name: newPresetName,
      uuid: uuidv4(),
      annotationStyles: {
        ...aStyles,
      },
    };

    props.onSavePreset(newPreset);

    setNewPresetName("");
  };

  const handleSavePresetEnter = async (e: any) => {
    if (e.key === "Enter") {
      e.preventDefault();

      savePreset();
    }
  };

  const handleChangePresetName = (e: any) =>
    setNewPresetName(e.currentTarget.value);

  if (!a.fontFamily) return <div></div>;

  return (
    <Paper elevation={2} sx={{ padding: 4 }} className="imageEditorOptions">
      <Stack spacing={3}>
        <PresetSelector
          selectPreset={selectPreset}
          deletePreset={props.onDeletePreset}
          presets={props.presets}
        />
        <ImageEditorSubtitle>Font Appearance</ImageEditorSubtitle>
        <FormControl fullWidth>
          <InputLabel>Font Type</InputLabel>
          <Select
            variant="standard"
            onChange={updateFontFamily}
            value={a.fontFamily}
            sx={{
              textOverflow: "ellipsis !important",
              overflowX: "hidden !important",
              display: "grid !important",
            }}
          >
            {props.fontFamilies.map((ff) => (
              <MenuItem value={ff} dense key={ff}>
                {ff}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <Stack spacing={2} sx={{ alignItems: "center" }}>
          <Typography
            variant="caption"
            sx={{ color: "rgba(255, 255, 255, 0.7)" }}
          >
            Font Color
          </Typography>
          <section className="small-color-picker">
            <HexColorPicker
              color={a.fontColor}
              onChange={updateFontColor}
              defaultValue={a.fontColor}
            />
          </section>
        </Stack>
        <TextField
          label="Font Size"
          variant="standard"
          type="number"
          onChange={updateFontSize}
          value={a.fontSize}
        />
        <TextField
          label="Stroke Size"
          variant="standard"
          type="number"
          onChange={updateStrokeSize}
          value={a.strokeSize}
          helperText="This is relative to font size."
        />
        <Fade in={a.strokeSize > 0} unmountOnExit>
          <Stack
            spacing={2}
            sx={{ alignItems: "center", width: "100%", display: "flex" }}
          >
            <Typography
              variant="caption"
              sx={{ color: "rgba(255, 255, 255, 0.7)" }}
            >
              Stroke Color
            </Typography>
            <section className="small-color-picker">
              <HexColorPicker
                color={a.strokeColor}
                onChange={updateStrokeColor}
                defaultValue={a.strokeColor}
              />
            </section>
          </Stack>
        </Fade>
        <FormControlLabel
          control={<Checkbox onChange={updateBold} checked={a.isBold} />}
          label="Bold"
        />
        <FormControlLabel
          control={<Checkbox onChange={updateItalic} checked={a.isItalic} />}
          label="Italic"
        />
        <ImageEditorSubtitle>Font Placement</ImageEditorSubtitle>
        <FormControl fullWidth>
          <InputLabel>Horizontal Alignment</InputLabel>
          <Select
            variant="standard"
            onChange={updateTextAlign}
            value={a.textAlign}
          >
            <MenuItem value={"left"} dense>
              Left
            </MenuItem>
            <MenuItem value={"center"} dense>
              Center
            </MenuItem>
            <MenuItem value={"right"} dense>
              Right
            </MenuItem>
          </Select>
        </FormControl>
        <FormControlLabel
          control={
            <Checkbox
              onChange={updateVerticalCenter}
              checked={a.verticalCenter}
            />
          }
          label="Center Vertically"
        />
        <ImageEditorSubtitle>Box Appearance</ImageEditorSubtitle>
        <FormControlLabel
          control={
            <Checkbox
              onChange={updateHasBackgroundColor}
              checked={a.hasBackgroundColor}
            />
          }
          label="Background Color"
        />
        <Fade in={a.hasBackgroundColor} unmountOnExit>
          <Stack
            spacing={2}
            sx={{ alignItems: "center", width: "100%", display: "flex" }}
          >
            <Typography variant="body1">Background Color</Typography>
            <section className="small-color-picker">
              <HexColorPicker
                color={a.backgroundColor}
                onChange={updateBackgroundColor}
                defaultValue={a.backgroundColor}
              />
            </section>
          </Stack>
        </Fade>
        <Fade in={a.hasBackgroundColor} unmountOnExit>
          <TextField
            label="Background Border Radius"
            variant="standard"
            type="number"
            onChange={updateBorderRadius}
            value={a.borderRadius}
            fullWidth
          />
        </Fade>
        <ImageEditorSubtitle>Actions</ImageEditorSubtitle>
        <Button
          variant="outlined"
          onClick={handleDeleteAnnotation}
          color="secondary"
          sx={{ marginTop: 8 }}
        >
          Delete Text
        </Button>
        <TextField
          sx={{ marginTop: 8 }}
          label="Save Preset As"
          variant="standard"
          onKeyDown={handleSavePresetEnter}
          value={newPresetName}
          onChange={handleChangePresetName}
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton onClick={savePreset} color="primary" edge="end">
                  <ArrowCircleRightIcon />
                </IconButton>
              </InputAdornment>
            ),
          }}
        />
      </Stack>
    </Paper>
  );
};

export default ImageEditorOptions;
