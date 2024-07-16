import { TextField } from "@mui/material";
import React from "react";

const tryParseFloat = (
  val: any,
  defaultValue: number,
  minValue: number,
  maxValue: number
) => {
  try {
    const parsed = parseFloat(val);
    if (Number.isNaN(parsed) || parsed < minValue || parsed > maxValue)
      throw Error("Invalid value!");

    return parsed;
  } catch (err) {
    return defaultValue;
  }
};

const tryParseInt = (
  val: any,
  defaultValue: number,
  minValue: number,
  maxValue: number
) => {
  try {
    const parsed = parseInt(val, 10);
    if (Number.isNaN(parsed) || parsed < minValue || parsed > maxValue)
      throw Error("Invalid value!");

    return parsed;
  } catch (err) {
    return defaultValue;
  }
};

const gv = (val: number | undefined | null, defaultVal: number) => {
  if (val === null || val === undefined) return defaultVal;
  return val;
};

export type UpdateNumberFieldProps = {
  changeValue: (key: string, value: string | number) => void;
  keyName: string;
  defaultValue: string | number;
  helperText?: string;
  placeholder?: string;
  label: string;
  minValue?: number;
  maxValue?: number;
  safeValue?: number;
  valueType: "float" | "int";
};

const UpdateNumberField = (props: UpdateNumberFieldProps) => {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;

    if (props.valueType === undefined || props.safeValue === undefined) {
      props.changeValue(props.keyName, newValue);
    } else if (props.valueType === "int") {
      const parsed = tryParseInt(
        newValue,
        props.safeValue,
        gv(props.minValue, -100),
        gv(props.maxValue, 99999)
      );
      props.changeValue(props.keyName, parsed);
    } else if (props.valueType === "float") {
      const parsed = tryParseFloat(
        newValue,
        props.safeValue,
        gv(props.minValue, -100),
        gv(props.maxValue, 99999)
      );
      props.changeValue(props.keyName, parsed);
    }
  };

  return (
    <TextField
      label={props.label}
      variant="standard"
      type="number"
      onChange={handleChange}
      defaultValue={props.defaultValue}
      helperText={props.helperText}
      placeholder={props.placeholder}
    />
  );
};

export default UpdateNumberField;
