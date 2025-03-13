import {
  Checkbox,
  FormControlLabel,
  FormGroup,
  FormHelperText,
} from "@mui/material";
import React from "react";

export type UpdateCheckboxProps = {
  changeValue: (key: string, value: boolean) => void;
  keyName: string;
  defaultValue: boolean;
  helperText?: string;
  label: string;
  style?: any;
};

const UpdateCheckbox = (props: UpdateCheckboxProps) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) =>
    props.changeValue(props.keyName, e.currentTarget.checked);

  const contr = (
    <FormGroup style={props.style}>
      <FormControlLabel
        control={
          <Checkbox
            onChange={handleChange}
            defaultChecked={props.defaultValue}
          />
        }
        label={props.label}
      />
      {props.helperText && <FormHelperText>{props.helperText}</FormHelperText>}
    </FormGroup>
  );

  return contr;
};

export default UpdateCheckbox;
