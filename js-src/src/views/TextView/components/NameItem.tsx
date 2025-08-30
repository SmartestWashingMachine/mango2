import React, { useState } from "react";
import { ListItem, ListItemButton, ListItemText } from "@mui/material";

type NameItemProps = {
  sourceName: string;
  suggestedTranslation: string;
  gender: string;
  isLast?: boolean;
  isBrief?: boolean;
  onSelect: (
    sourceName: string,
    suggestedTranslation: string,
    gender: string
  ) => void;
};

const NameItem = ({
  sourceName,
  suggestedTranslation,
  gender,
  isLast,
  isBrief,
  onSelect,
}: NameItemProps) => {
  const [wasSelected, setWasSelected] = useState(false);

  const selectName = () => {
    setWasSelected(true);
    onSelect(sourceName, suggestedTranslation, gender);
  };

  return (
    <ListItem dense divider={!isLast && !isBrief}>
      <ListItemButton onClick={selectName}>
        <ListItemText
          primaryTypographyProps={{
            sx: {
              color: !wasSelected ? "#e6a5f2ff" : "rgba(255, 255, 255, 0.7)",
              fontStyle: "italic",
            },
          }}
          secondaryTypographyProps={{
            sx: {
              fontStyle: "italic",
            },
          }}
          sx={{ overflowWrap: "break-word" }}
          primary={<>Found Name: {sourceName}</>}
          secondary={
            <>
              This name was automatically detected. Click to specify how it
              should be translated.
            </>
          }
        />
      </ListItemButton>
    </ListItem>
  );
};

export default NameItem;
