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

const chunkTip = "Images can be split into small chunks for better text detection at the cost of speed. The translated image chunks will then be merged for the final image.";

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
    <MenuItem
      value={x.value}
      dense
      disabled={!itemEnabled(x)}
    >
      {x.name}
    </MenuItem>,
    <MenuItem disabled value="" divider dense>
      <em style={{ fontSize: "small" }}>{x.desc}</em>
    </MenuItem>,
  ];

  const itemEnabled = (x: { name: string; value: string; desc: string }) => {
    return (props.installedModels.indexOf(x.value) !== -1) || (x.name === "None");
  };

  // Since UpdateNumberField uses defaultValues.
  if (props.tileWidth === -1 || props.tileHeight === -1) return null;

  return (
    <Paper elevation={2} sx={{ padding: 4 }}>
      <Stack spacing={4}>
        <Stack direction={{ sm: "column", md: "row", }} spacing={{ sm: 4, md: 8, }}>
          <UpdateNumberField
            label="Tile Width %"
            changeValue={(_, val: any) => props.onChangeTileWidth(val)}
            keyName="tileWidth"
            defaultValue={props.tileWidth}
            valueType="int"
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
            valueType="int"
            safeValue={100}
            minValue={1}
            maxValue={100}
            tooltip={chunkTip}
          />
        </Stack>
        <FormControl fullWidth>
          <InputLabel>Cleaning Mode</InputLabel>
          <Select
            variant="standard"
            onChange={updateCleaningMode}
            value={props.cleaningMode}
          >
            {CLEANING_OPTIONS.map(renderItem)}
          </Select>
        </FormControl>
        <FormControl fullWidth>
          <InputLabel>Redrawing Mode</InputLabel>
          <Select
            variant="standard"
            onChange={updateRedrawingMode}
            value={props.redrawingMode}
          >
            {REDRAWING_OPTIONS.map(renderItem)}
          </Select>
        </FormControl>
      </Stack>
    </Paper>
  );
};

export default ImageViewOptions;
