import { CssBaseline, Typography } from "@mui/material";
import React, { useEffect } from "react";

export type LensBoxProps = {
  text: string | null | undefined;
};

const LensBox = (props: LensBoxProps) => {
  useEffect(() => {
    document.body.style.backgroundColor = "rgba(255, 255, 255, 0.0)"; // This gives a transparent window.
  }, []);

  const boxStyles = {
    backgroundColor: "rgba(255, 255, 255, 0.75)",
    padding: "8px",
    borderRadius: "4px",
    width: "100%",
    height: "100%",
    overflow: "auto",
  };

  const textStyles = {
    fontFamily: '"ocrbox.otf", "ocrbox.ttf", Roboto, "Roboto", Arial',
    color: "black",
    paintOrder: "stroke fill", // Necessary for pretty strokes.
    fontSize: `10px`,
    whiteSpace: "pre-line",
  };

  return (
    <CssBaseline>
      <div style={boxStyles}>
        <Typography variant="body1" sx={textStyles}>
          {props.text}
        </Typography>
      </div>
    </CssBaseline>
  );
};

export default LensBox;
