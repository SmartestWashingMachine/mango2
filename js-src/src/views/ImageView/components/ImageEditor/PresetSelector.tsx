import React, { useState } from "react";
import { Button, IconButton, ListItem, Menu } from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import ITextPreset from "../../../../types/TextPreset";

export type PresetSelectorProps = {
  selectPreset: (e: any) => void;
  deletePreset: (uuid: string) => void;
  presets: ITextPreset[];
  buttonText?: string;
  color?: any;
};

const PresetSelector = (props: PresetSelectorProps) => {
  const [presetMenuAnchor, setPresetMenuAnchor] = useState<HTMLElement | null>(
    null
  );
  const openPresetMenu = (e: any) => setPresetMenuAnchor(e.currentTarget);
  const closePresetMenu = () => setPresetMenuAnchor(null);

  const handleSelectPreset = (e: any) => {
    closePresetMenu();
    props.selectPreset(e);
  };

  const handleDeletePreset = (uuid: string) => {
    closePresetMenu();
    props.deletePreset(uuid);
  };

  if (props.presets === null || props.presets === undefined) {
    return null;
  }

  return (
    <>
      <Button
        color={props.color || "primary"}
        sx={{ marginBottom: 8 }}
        onClick={openPresetMenu}
        disabled={props.presets.length === 0}
      >
        {props.buttonText || "Use Preset"}
      </Button>
      <Menu
        open={!!presetMenuAnchor}
        onClose={closePresetMenu}
        anchorEl={presetMenuAnchor}
      >
        {props.presets.map((p) => (
          <ListItem dense key={p.uuid} value={p.uuid} sx={{ width: "100%" }}>
            <Button
              value={p.uuid}
              onClick={handleSelectPreset}
              fullWidth
              color="info"
            >
              {p.name}
            </Button>
            <IconButton onClick={() => handleDeletePreset(p.uuid)}>
              <CloseIcon />
            </IconButton>
          </ListItem>
        ))}
      </Menu>
    </>
  );
};

export default PresetSelector;
