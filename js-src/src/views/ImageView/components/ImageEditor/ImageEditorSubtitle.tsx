import { Typography } from "@mui/material";
import React from "react";

export type ImageEditorSubtitleProps = {
  children: string;
};

const ImageEditorSubtitle = (props: ImageEditorSubtitleProps) => {
  return (
    <Typography
      variant="overline"
      align="center"
      sx={{ color: "hsl(291, 3%, 74%)", marginBottom: 4 }}
    >
      {props.children}
    </Typography>
  );
};

export default ImageEditorSubtitle;
