import {
  Button,
  Checkbox,
  Divider,
  FormControlLabel,
  Grid,
  IconButton,
  MenuItem,
  Stack,
  TextField,
  Typography,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import React from "react";
import IReplaceTerm from "../../../types/ReplaceTerm";
import RemoveIcon from "@mui/icons-material/Remove";
import TermPreviewBox from "./TermPreviewBox";

export type ReplaceTermsListProps = {
  terms: IReplaceTerm[];
  updateTerm: (
    termUuid: string,
    termKey: keyof IReplaceTerm,
    termValue: string | boolean
  ) => void;
  createTerm: () => void;
  removeTerm: (termUuid: string) => void;
  importTerms: () => void;
  exportTerms: () => void;
};

type TermProps = {
  t: IReplaceTerm;
} & Pick<ReplaceTermsListProps, "updateTerm" | "removeTerm">;

const Term = (props: TermProps) => {
  const { updateTerm, removeTerm, t } = props;

  const theme = useTheme();
  const matchDownMd = useMediaQuery(theme.breakpoints.down("sm"));

  const content = (
    <>
      <TextField
        placeholder="Pattern"
        variant="outlined"
        onChange={(e) => updateTerm(t.uuid, "original", e.currentTarget.value)}
        defaultValue={t.original}
        fullWidth
        multiline
        size="small"
      />
      <TextField
        placeholder="Replacement"
        variant="outlined"
        onChange={(e) =>
          updateTerm(t.uuid, "replacement", e.currentTarget.value)
        }
        defaultValue={t.replacement}
        fullWidth
        multiline
        size="small"
      />
      <TextField
        onChange={(e) => updateTerm(t.uuid, "onSide", e.target.value)}
        defaultValue={t.onSide}
        variant="outlined"
        select
        fullWidth
        size="small"
      >
        <MenuItem value="source">Source Side</MenuItem>
        <MenuItem value="target">Target Side</MenuItem>
      </TextField>
      <FormControlLabel
        control={
          <Checkbox
            onChange={(e) =>
              updateTerm(t.uuid, "enabled", e.currentTarget.checked)
            }
            checked={t.enabled || false}
            color="info"
          />
        }
        label={matchDownMd ? "Enabled" : ""}
        color="info"
      />
      {matchDownMd ? (
        <Button
          variant="outlined"
          onClick={() => removeTerm(t.uuid)}
          color="error"
        >
          Remove
        </Button>
      ) : (
        <IconButton onClick={() => removeTerm(t.uuid)}>
          <RemoveIcon />
        </IconButton>
      )}
    </>
  );

  if (matchDownMd) {
    return (
      <Stack
        spacing={1}
        direction="column"
        key={t.uuid}
        justifyContent="space-around"
        sx={{ opacity: t.enabled ? 1 : 0.5, marginTop: 2, marginBottom: 8 }}
      >
        {content}
      </Stack>
    );
  } else
    return (
      <Stack
        spacing={2}
        direction="row"
        key={t.uuid}
        justifyContent="space-around"
        sx={{ opacity: t.enabled ? 1 : 0.5, marginTop: 2 }}
      >
        {content}
      </Stack>
    );
};

const ReplaceTermsList = ({
  terms,
  updateTerm,
  createTerm,
  removeTerm,
  importTerms,
  exportTerms,
}: ReplaceTermsListProps) => {
  return (
    <Stack spacing={2}>
      <Grid
        container
        direction="row"
        alignItems="center"
        justifyItems="center"
        justifyContent="center"
      >
        <Grid item>
          <Typography align="center" variant="body2">
            Terms on the left will be replaced with the terms on the right if
            they are found. Untick a checkbox to disable that term for the time
            being. Supports regex - be careful with untrusted input!
          </Typography>
        </Grid>
      </Grid>
      {terms.map((t) => (
        <Term
          t={t}
          updateTerm={updateTerm}
          removeTerm={removeTerm}
          key={t.uuid}
        />
      ))}
      <Button variant="outlined" color="primary" onClick={createTerm}>
        Create Term
      </Button>
      <Stack direction="row" spacing={2}>
        <Button
          variant="outlined"
          color="secondary"
          onClick={importTerms}
          fullWidth
        >
          Import Terms
        </Button>
        <Button variant="outlined" color="info" onClick={exportTerms} fullWidth>
          Export Terms
        </Button>
      </Stack>
      <Divider
        sx={{ marginTop: "16px !important", marginBottom: "16px !important" }}
      />
      <TermPreviewBox terms={terms} />
    </Stack>
  );
};

export default ReplaceTermsList;
