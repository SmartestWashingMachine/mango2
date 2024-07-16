import { TextField } from "@mui/material";
import React from "react";

export type UpdateListFieldProps = {
  changeValue: (key: string, value: string) => void;
  keyName: string;
  defaultValue: string;
  helperText?: string;
  placeholder?: string;
  label: string;
  children: React.ReactNode;
};

const UpdateListField = (props: UpdateListFieldProps) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) =>
    props.changeValue(props.keyName, e.target.value);

  return (
    <TextField
      select
      label={props.label}
      variant="standard"
      onChange={handleChange}
      defaultValue={props.defaultValue}
      helperText={props.helperText}
      placeholder={props.placeholder}
    >
      {props.children}
    </TextField>
  );
};

export default UpdateListField;
