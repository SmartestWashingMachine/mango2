import React, { useCallback, useState } from "react";
import BaseView from "./BaseView";
import TextField from "@mui/material/TextField";
import InputAdornment from "@mui/material/InputAdornment";
import ArrowCircleRightIcon from "@mui/icons-material/ArrowRight";
import {
  Button,
  FormControlLabel,
  FormGroup,
  IconButton,
  List,
  ListItemButton,
  ListItemText,
  Stack,
  Switch,
  Typography,
} from "@mui/material";
import { pollTranslateWebStatus, translateWeb } from "../flaskcomms/webViewComms";
import { useLoader } from "../components/LoaderContext";

const WebView = () => {
  const [text, setText] = useState("");
  const [contentFilter, setContentFilter] = useState('div[id="novel_honbun"]');
  const [output, setOutput] = useState("");

  const [preview, setPreview] = useState(true);

  const { loading, setLoading } = useLoader();

  const handleTextChange = (e: any) => setText(e.currentTarget.value);

  const handleContentFilterChange = (e: any) =>
    setContentFilter(e.currentTarget.value);

  const handlePreviewChange = (e: any) => setPreview(e.target.checked);

  const doneTranslatingItem = useCallback(
    async (newOutput: string) => {
      setOutput(newOutput);
    },
    []
  );

  const doneTranslatingPage = useCallback(async () => {
    setLoading(false);
  }, []);

  const processWeb = async () => {
    if (loading) return;

    setLoading(true);

    await pollTranslateWebStatus(
      doneTranslatingItem,
      doneTranslatingPage,
    ); // Create a websocket to listen to the server for progress and the end result.
    await translateWeb(text, contentFilter, preview);
  };

  const handleProcessTextEnter = async (e: any) => {
    if (e.key === "Enter") {
      e.preventDefault();

      await processWeb();
    }
  };

  const handleCopyText = (t: string) => {
    navigator.clipboard.writeText(t);
  };

  return (
    <BaseView>
      <Stack spacing={6} direction="row" sx={{ width: "95%" }}>
        <Stack spacing={4}>
          <TextField
            onChange={handleTextChange}
            value={text}
            placeholder="Link"
            onKeyDown={handleProcessTextEnter}
            fullWidth
            helperText="Enter a webpage link. The model will attempt to translate all text in the selected elements."
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={processWeb}
                    disabled={loading}
                    color="primary"
                    edge="end"
                  >
                    <ArrowCircleRightIcon />
                  </IconButton>
                </InputAdornment>
              ),
            }}
          />
          <TextField
            onChange={handleContentFilterChange}
            value={contentFilter}
            placeholder="Content Filter"
            onKeyDown={handleProcessTextEnter}
            fullWidth
            helperText="You can specify selectors to only translate the contents of certain HTML elements."
          />
          <Stack spacing={0} sx={{ justifyContent: "center" }}>
            <FormGroup sx={{ alignContent: "center" }}>
              <FormControlLabel
                control={
                  <Switch checked={preview} onChange={handlePreviewChange} />
                }
                label="Preview Selected Elements"
              />
            </FormGroup>
          </Stack>
          {loading && (
            <Typography
              variant="body2"
              align="center"
              sx={{ color: "hsl(291, 3%, 74%)" }}
              textAlign="center"
            >
              Loading...
            </Typography>
          )}
        </Stack>
        <Stack spacing={2}>
          {output.length > 0 ? (
            <>
              <List
                dense
                sx={{ display: "grid", overflowY: "auto", maxHeight: "80vh" }}
              >
                {output.split("\n\n").map((o, i) => (
                  <ListItemButton key={i} onClick={() => handleCopyText(o)}>
                    <ListItemText primary={o} />
                  </ListItemButton>
                ))}
              </List>
              <Button fullWidth onClick={() => handleCopyText(output)}>
                Copy All
              </Button>
            </>
          ) : (
            <Typography
              variant="body2"
              align="center"
              sx={{ color: "hsl(291, 3%, 74%)" }}
            >
              The output will show here.
            </Typography>
          )}
        </Stack>
      </Stack>
    </BaseView>
  );
};

export default WebView;
