import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Typography,
} from "@mui/material";
import React from "react";

export type BaseHelpProps = {
  title: string;
  steps: string[];
};

const BaseHelp = ({ title, steps }: BaseHelpProps) => {
  return (
    <Accordion>
      <AccordionSummary>{title}</AccordionSummary>
      <AccordionDetails>
        {steps.map((s, i) => (
          <React.Fragment key={s}>
            <Typography sx={{ marginBottom: 2 }}>{s}</Typography>
          </React.Fragment>
        ))}
      </AccordionDetails>
    </Accordion>
  );
};

export default BaseHelp;
