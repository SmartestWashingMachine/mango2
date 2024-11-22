import React from "react";
import {
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Tooltip,
} from "@mui/material";
import { CLEANING_OPTIONS } from "../../../../utils/appOptions/cleaningOptions";
import { REDRAWING_OPTIONS } from "../../../../utils/appOptions/redrawingOptions";
import UpdateNumberField from "../../../../components/UpdateNumberField";

const chunkTip =
  "Images can be split into small chunks for better text detection at the cost of speed. The translated image chunks will then be merged for the final image. Translating webtoons? Try setting the Tile Height to -1.";

export type ImageViewOptionsProps = {
  cleaningMode: string;
  redrawingMode: string;
  onChangeCleaningMode: (mode: string) => void;
  onChangeRedrawingMode: (mode: string) => void;
  installedModels: string[];
  tileWidth: number;
  tileHeight: number;
  onChangeTileWidth: (val: number) => void;
  onChangeTileHeight: (val: number) => void;
};

const ImageViewOptions = (props: ImageViewOptionsProps) => {
  const updateCleaningMode = (e: any) => {
    props.onChangeCleaningMode(e.target.value);
  };

  const updateRedrawingMode = (e: any) => {
    props.onChangeRedrawingMode(e.target.value);
  };

  const renderItem = (x: { name: string; value: string; desc: string }) => [
    <MenuItem value={x.value} dense disabled={!itemEnabled(x)}>
      {x.name}
    </MenuItem>,
    <MenuItem disabled value="" divider dense>
      <em style={{ fontSize: "small" }}>{x.desc}</em>
    </MenuItem>,
  ];

  const itemEnabled = (x: { name: string; value: string; desc: string }) => {
    return props.installedModels.indexOf(x.value) !== -1 || x.name === "None";
  };

  // Since UpdateNumberField uses defaultValues.
  if (props.tileWidth === -2000 || props.tileHeight === -2000) return null;

  const checkSpecialMode = () => {
    if (props.tileHeight === -1) return "Short Webtoon Mode";
    if (props.tileHeight === 0) return "Long Webtoon Mode";
    return " ";
  };

  return (
    <Paper elevation={2} sx={{ padding: 3 }}>
      <Stack spacing={2}>
        <Stack
          direction={{ sm: "column", lg: "row" }}
          spacing={{ sm: 2, lg: 6 }}
        >
          <UpdateNumberField
            label="Tile Width %"
            changeValue={(_, val: any) => props.onChangeTileWidth(val)}
            keyName="tileWidth"
            defaultValue={props.tileWidth}
            valueType="float"
            safeValue={100}
            minValue={1}
            maxValue={100}
            tooltip={chunkTip}
          />
          <UpdateNumberField
            label="Tile Height %"
            changeValue={(_, val: any) => props.onChangeTileHeight(val)}
            keyName="tileHeight"
            defaultValue={props.tileHeight}
            valueType="float"
            safeValue={100}
            minValue={-1}
            maxValue={100}
            tooltip={chunkTip}
            helperText={checkSpecialMode()}
            color={props.tileHeight <= 0 ? "warning" : undefined}
          />
        </Stack>
        <FormControl fullWidth variant="standard">
          <InputLabel>Cleaning Mode</InputLabel>
          <Select
            onChange={updateCleaningMode}
            value={props.cleaningMode}
            label="Cleaning Mode"
          >
            {CLEANING_OPTIONS.map(renderItem)}
          </Select>
        </FormControl>
        <FormControl fullWidth variant="standard">
          <InputLabel>Redrawing Mode</InputLabel>
          <Select
            onChange={updateRedrawingMode}
            value={props.redrawingMode}
            label="Redrawing Mode"
          >
            {REDRAWING_OPTIONS.map(renderItem)}
          </Select>
        </FormControl>
      </Stack>
    </Paper>
  );
};

export default ImageViewOptions;
