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
};

const ImageViewOptions = (props: ImageViewOptionsProps) => {
  const updateCleaningMode = (e: any) => {
    props.onChangeCleaningMode(e.target.value);
  };

  const updateRedrawingMode = (e: any) => {
    props.onChangeRedrawingMode(e.target.value);
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
            {CLEANING_OPTIONS.map((x) => [
              <MenuItem value={x.value} dense>
                {x.name}
              </MenuItem>,
              <MenuItem disabled value="" divider dense>
                <em style={{ fontSize: "small" }}>{x.desc}</em>
              </MenuItem>,
            ])}
          </Select>
        </FormControl>
        <FormControl fullWidth>
          <InputLabel>Redrawing Mode</InputLabel>
          <Select
            variant="standard"
            onChange={updateRedrawingMode}
            value={props.redrawingMode}
          >
            {REDRAWING_OPTIONS.map((x) => [
              <MenuItem value={x.value} dense>
                {x.name}
              </MenuItem>,
              <MenuItem disabled value="" divider dense>
                <em style={{ fontSize: "small" }}>{x.desc}</em>
              </MenuItem>,
            ])}
          </Select>
        </FormControl>
      </Stack>
    </Paper>
  );
};

export default ImageViewOptions;
