import React from "react";
import {
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
} from "@mui/material";
import { CLEANING_OPTIONS } from "../../../../utils/appOptions/cleaningOptions";
import { REDRAWING_OPTIONS } from "../../../../utils/appOptions/redrawingOptions";

export type ImageViewOptionsProps = {
  cleaningMode: string;
  redrawingMode: string;
  onChangeCleaningMode: (mode: string) => void;
  onChangeRedrawingMode: (mode: string) => void;
  installedModels: string[];
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
    return props.installedModels.indexOf(x.value) !== -1;
  };

  return (
    <Paper elevation={2} sx={{ padding: 4 }}>
      <Stack spacing={4}>
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
