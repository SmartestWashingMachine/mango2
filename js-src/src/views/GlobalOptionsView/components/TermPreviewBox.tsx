import React, { useState } from "react";
import IReplaceTerm from "../../../types/ReplaceTerm";
import { Stack, TextField } from "@mui/material";

export type TermPreviewBoxProps = {
  terms: IReplaceTerm[];
};

const useTermsOnSide = (
  value: string,
  terms: IReplaceTerm[],
  onSide: string
) => {
  let newValue = value;

  try {
    for (const t of terms) {
      if (t.onSide === onSide && t.enabled) {
        // This isn't perfect at all.. and there's still other differences between python's re.sub and JS replaceAll.
        // But it should be okay for simple cases, hopefully?
        const pyToJsReplacement = t.replacement
          .replaceAll(/\\([0-9])/g, "$fakedummytext$1")
          .replaceAll("fakedummytext", "");

        newValue = newValue.replaceAll(
          new RegExp(t.original, "g"),
          pyToJsReplacement
        );
      }
    }
  } catch (err) {
    console.log(err);
    newValue = "ERROR";
  }

  return newValue;
};

const DEFAULT_SOURCE = "Example source text";
const DEFAULT_TARGET = "Example translated text";

const TermPreviewBox = (props: TermPreviewBoxProps) => {
  const [sourceText, setSourceText] = useState(DEFAULT_SOURCE);
  const [targetText, setTargetText] = useState(DEFAULT_TARGET);

  const handleSourceChange = (e: React.ChangeEvent<HTMLInputElement>) =>
    setSourceText(e.currentTarget.value);
  const handleTargetChange = (e: React.ChangeEvent<HTMLInputElement>) =>
    setTargetText(e.currentTarget.value);

  return (
    <Stack spacing={2}>
      <Stack spacing={4} direction="row">
        <TextField
          label="Sample source / target"
          onChange={handleSourceChange}
          defaultValue={DEFAULT_SOURCE}
          fullWidth
        />
        <TextField
          label="Transformed source / target"
          disabled
          value={useTermsOnSide(sourceText, props.terms, "source")}
          fullWidth
        />
      </Stack>
      <Stack spacing={4} direction="row">
        <TextField
          onChange={handleTargetChange}
          defaultValue={DEFAULT_TARGET}
          fullWidth
        />
        <TextField
          disabled
          value={useTermsOnSide(targetText, props.terms, "target")}
          fullWidth
        />
      </Stack>
    </Stack>
  );
};

export default TermPreviewBox;
