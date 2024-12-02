import {
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListSubheader,
  Paper,
} from "@mui/material";
import React from "react";

const limitUpTo = <T extends any>(arr: T[], limit: number) => {
  if (!arr || arr.length <= limit) return arr;

  return arr.slice(0, limit);
};

const cutOffText = (t: string) => (t?.length > 14 ? `${t.slice(0, 12)}...` : t);

export type ImageProgressListProps = {
  pendingImageNames: string[];
  /** The progress (from 0 to 100) of the currently pending image. */
  curProgress: number;
  dense?: boolean;
};

const ImageProgressList = ({
  pendingImageNames,
  curProgress,
  dense,
}: ImageProgressListProps) => {
  let items = null;
  if (!dense) {
    items = (
      <>
        {limitUpTo(pendingImageNames, 3).map((img, idx) => (
          <ListItem key={img}>
            <ListItemText
              primary={cutOffText(img)}
              secondary={
                <LinearProgress
                  color="primary"
                  variant="determinate"
                  value={idx === 0 ? curProgress : 0}
                  sx={{ marginTop: 2 }}
                />
              }
            ></ListItemText>
          </ListItem>
        ))}
        {pendingImageNames.length > 3 && (
          <ListItem dense>
            <ListItemText secondary={`${pendingImageNames.length - 3} more`} />
          </ListItem>
        )}
      </>
    );
  } else if (pendingImageNames.length > 0) {
    items = (
      <>
        <ListItem dense>
          <ListItemText
            primary={cutOffText(pendingImageNames[0])}
            secondary={
              <LinearProgress
                color="primary"
                variant="determinate"
                value={curProgress}
                sx={{ marginTop: 1 }}
                key={pendingImageNames[0] || "prog"}
              />
            }
          ></ListItemText>
        </ListItem>
        {pendingImageNames.length > 1 && (
          <ListItem dense>
            <ListItemText secondary={`${pendingImageNames.length - 1} more`} />
          </ListItem>
        )}
      </>
    );
  }

  return (
    <Paper elevation={2}>
      <List subheader={<ListSubheader>Progress</ListSubheader>} dense={dense}>
        {items}
      </List>
    </Paper>
  );
};

export default ImageProgressList;
