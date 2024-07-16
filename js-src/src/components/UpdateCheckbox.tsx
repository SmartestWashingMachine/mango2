import {
  Checkbox,
  FormControlLabel,
  FormGroup,
  FormHelperText,
  Tooltip,
} from "@mui/material";
import React from "react";

export type UpdateCheckboxProps = {
  changeValue: (key: string, value: boolean) => void;
  keyName: string;
  defaultValue: boolean;
  tooltip: string;
  helperText?: string;
  label: string;
};

const UpdateCheckbox = (props: UpdateCheckboxProps) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) =>
    props.changeValue(props.keyName, e.currentTarget.checked);

  return (
    <Tooltip title={props.tooltip} placement="top-start" enterDelay={1000}>
      <FormGroup>
        <FormControlLabel
          control={
            <Checkbox
              onChange={handleChange}
              defaultChecked={props.defaultValue}
            />
          }
          label={props.label}
        />
        {props.helperText && (
          <FormHelperText>{props.helperText}</FormHelperText>
        )}
      </FormGroup>
    </Tooltip>
  );
};

export default UpdateCheckbox;
