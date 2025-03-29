import {
  Button,
  Divider,
  Grid,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import React, { useState } from "react";

export type PaginatedTabsProps = {
  items: {
    [category: string]: {
      [searchName: string]: any;
    };
  };
  headers?: any;
  footers?: any;
  showItems?: boolean;
  itemsKey?: string;
  boldFirst?: boolean;
};

const PaginatedTabs = (props: PaginatedTabsProps) => {
  const [category, setCategory] = useState("");
  const [search, setSearch] = useState("");

  const keys = Object.keys(props.items);

  const searchInStr = (other: string) =>
    other.toLowerCase().includes(search.toLowerCase().trim());

  const lookforElements = () => {
    for (const itemKey of keys) {
      const item = props.items[itemKey];

      const entries = Object.entries(item);
      if (searchInStr(itemKey)) {
        return entries.map((x) => (
          <React.Fragment key={x[0]}>{x[1]}</React.Fragment>
        ));
      }

      for (let i = 0; i < entries.length; i++) {
        const searchName = entries[i][0];

        // Return this element and all others after it.
        if (searchInStr(searchName)) {
          return entries
            .slice(i)
            .map((x) => <React.Fragment key={x[0]}>{x[1]}</React.Fragment>);
        }
      }
    }

    return <div></div>;
  };

  const flattenElements = () => {
    const item = props.items[category];
    if (!item) {
      if (props.items !== null && props.items !== undefined) {
        const firstCategory = Object.keys(props.items);
        if (firstCategory.length > 0) {
          return Object.entries(props.items[firstCategory[0]]).map((x) => (
            <React.Fragment key={x[0]}>{x[1]}</React.Fragment>
          ));
        }
      }

      return <div></div>;
    }

    return Object.entries(item).map((x) => (
      <React.Fragment key={x[0]}>{x[1]}</React.Fragment>
    ));
  };

  const createHeaders = () => {
    if (!props.headers) return null;

    return (
      <Stack spacing={1}>
        {props.headers}
        <Divider />
      </Stack>
    );
  };

  const createFooters = () => {
    if (!props.footers) return null;

    return (
      <Stack spacing={3} sx={{ marginTop: "40px !important" }}>
        <Divider />
        {props.footers}
      </Stack>
    );
  };

  const selCategory = category || (keys.length > 0 ? keys[0] : "");

  return (
    <Stack spacing={2} sx={(theme) => ({ width: { xs: "100%", md: "75%" } })}>
      <TextField
        variant="outlined"
        placeholder="Search..."
        onChange={(e) => setSearch(e.currentTarget.value)}
        value={search}
        fullWidth
        size="small"
        autoFocus
      />
      <Grid
        container
        spacing={2}
        sx={{ minHeight: "90%" }}
        key={props.itemsKey || "items-key"}
      >
        <Grid item xs={3}>
          <Stack spacing={1} sx={{ padding: 2, height: "100%" }}>
            {createHeaders()}
            {keys.map((k, idx) => (
              <Button
                variant="text"
                key={k}
                onClick={() => {
                  setSearch("");
                  setCategory(k);
                }}
                color={"info"}
                sx={() => ({
                  fontWeight:
                    (props.boldFirst && idx === 0) || k === selCategory
                      ? "bold"
                      : "normal",
                  color: k === selCategory ? "white" : "hsl(291, 3%, 74%)",
                })}
                size={props.boldFirst && idx === 0 ? "medium" : "small"}
              >
                {k}
              </Button>
            ))}
            {createFooters()}
          </Stack>
        </Grid>
        <Divider orientation="vertical" flexItem sx={{ mr: "-1px" }} />
        <Grid item xs={9}>
          {props.showItems !== false && (
            <Stack spacing={2} sx={{ padding: 2 }}>
              {props.items[selCategory] && (
                <Typography align="center" variant="h6">
                  {selCategory}
                </Typography>
              )}
              {search.length === 0 ? flattenElements() : lookforElements()}
            </Stack>
          )}
        </Grid>
      </Grid>
    </Stack>
  );
};

export default PaginatedTabs;
