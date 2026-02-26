import {
  Button,
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
import RemoveIcon from "@mui/icons-material/Remove";
import INameEntry from "../../../types/NameEntry";

export type DictionaryListProps = {
  entries: INameEntry[];
  updateEntry: (uuid: string, k: keyof INameEntry, v: string | boolean) => void;
  createEntry: () => void;
  removeEntry: (termUuid: string) => void;
  importNames: () => void;
  exportNames: () => void;
};

type ItemProps = {
  t: INameEntry;
} & Pick<DictionaryListProps, "removeEntry" | "updateEntry">;

const Item = (props: ItemProps) => {
  const { updateEntry, removeEntry, t } = props;

  const theme = useTheme();
  const matchDownMd = useMediaQuery(theme.breakpoints.down("sm"));

  const content = (
    <>
      <TextField
        placeholder="Source Name"
        variant="outlined"
        onChange={(e) => updateEntry(t.uuid, "source", e.currentTarget.value)}
        defaultValue={t.source}
        fullWidth
        multiline
        size="small"
      />
      <TextField
        placeholder="Translated Name"
        variant="outlined"
        onChange={(e) => updateEntry(t.uuid, "target", e.currentTarget.value)}
        defaultValue={t.target}
        fullWidth
        multiline
        size="small"
      />
      <TextField
        select
        fullWidth
        size="small"
        label="Gender"
        variant="outlined"
        onChange={(e) => updateEntry(t.uuid, "gender", e.target.value)}
        defaultValue={t.gender}
      >
        <MenuItem value="">N/A</MenuItem>
        <MenuItem value="Male">Male</MenuItem>
        <MenuItem value="Female">Female</MenuItem>
      </TextField>
      {matchDownMd ? (
        <Button
          variant="outlined"
          onClick={() => removeEntry(t.uuid)}
          color="error"
        >
          Remove
        </Button>
      ) : (
        <IconButton onClick={() => removeEntry(t.uuid)}>
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
        sx={{ opacity: 1, marginTop: 2, marginBottom: 8 }}
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
        sx={{ opacity: 1, marginTop: 2 }}
      >
        {content}
      </Stack>
    );
};

const DictionaryList = ({
  entries,
  updateEntry,
  removeEntry,
  createEntry,
  importNames,
  exportNames,
}: DictionaryListProps) => {
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
            You can instruct the AI on how to translate certain names and
            entities here. This can be useful for translating names more
            effectively.
          </Typography>
        </Grid>
      </Grid>
      {entries.map((t) => (
        <Item
          t={t}
          updateEntry={updateEntry}
          removeEntry={removeEntry}
          key={t.uuid}
        />
      ))}
      <Button variant="outlined" color="primary" onClick={createEntry}>
        Create Entry
      </Button>
      <Stack direction="row" spacing={2}>
        <Button
          variant="outlined"
          color="secondary"
          onClick={importNames}
          fullWidth
        >
          Import Names
        </Button>
        <Button variant="outlined" color="info" onClick={exportNames} fullWidth>
          Export Names
        </Button>
      </Stack>
    </Stack>
  );
};

export default DictionaryList;
