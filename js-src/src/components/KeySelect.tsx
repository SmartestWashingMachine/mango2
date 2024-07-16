import React, { useState } from "react";
import { TextField, Tooltip } from "@mui/material";

type KeySelectProps = {
  onKeyChange: (key: string) => void;
  value: string;
  label: string;
  tooltip: string;
};

const KeySelect = ({ onKeyChange, value, label, tooltip }: KeySelectProps) => {
  const [keyValue, setKeyValue] = useState(value);

  const displayKey = (key: string) => {
    setKeyValue(key);
  };

  const handleKeyDown = (e: any) => {
    const { key } = e;

    if (key !== "Escape" && (!key.match(/[a-z]/i) || key.length !== 1)) {
      // This may not even be needed, but best to be safe for now...
      return; // Ensure it's a basic letter... for now.
    }

    onKeyChange(key);
    displayKey(key);
  };

  if (!value) {
    return null;
  }

  return (
    <Tooltip title={tooltip} placement="top-start">
      <TextField
        label={label}
        variant="standard"
        onKeyDown={handleKeyDown}
        value={keyValue === "Escape" ? "DISABLED" : keyValue}
      />
    </Tooltip>
  );
};

export default KeySelect;
