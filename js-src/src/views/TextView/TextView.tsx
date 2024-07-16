import React, { useCallback, useEffect, useState } from "react";
import BaseView from "../BaseView";
import TextField from "@mui/material/TextField";
import {
  Collapse,
  Grid,
  IconButton,
  Paper,
  Stack,
  Tooltip,
} from "@mui/material";
import ArrowCircleRightIcon from "@mui/icons-material/ArrowRight";
import HistoryPane from "./components/HistoryPane";
import IHistoryText from "../../types/HistoryText";
import { v4 as uuidv4 } from "uuid";
import DownloadIcon from "@mui/icons-material/Download";
import {
  pollTranslateTextStatus,
  translateText,
} from "../../flaskcomms/textViewComms";
import InputAdornment from "@mui/material/InputAdornment";
import MonitorIcon from "@mui/icons-material/Monitor";
import RefreshIcon from "@mui/icons-material/Refresh";
import SettingsIcon from "@mui/icons-material/SettingsOutlined";
import OpenInFullIcon from "@mui/icons-material/OpenInFull";
import AutoStoriesIcon from "@mui/icons-material/AutoStories";
import { useLoader } from "../../components/LoaderContext";
import { pTransformerJoin } from "../../utils/pTransformerJoin";
import { debugListeners } from "../../flaskcomms/debugListeners";
import { MainGateway } from "../../utils/mainGateway";

type TextViewProps = {
  onOpenOcrSettings: () => void;
};

const TextView = ({ onOpenOcrSettings }: TextViewProps) => {
  // Side view mode is more user-friendly for big text, or users who don't care for the backlog.
  const [isSideView, setIsSideView] = useState(false);

  const [texts, setTexts] = useState<IHistoryText[]>([]);

  const { loading, setLoading } = useLoader();

  // Users can input source language text to be processed in the backend into translated text.
  const [inputText, setInputText] = useState("");

  // Users can search for specific text in the backlog.
  const [search, setSearch] = useState("");

  /**
   * The list of UUIDs of history texts to use as context.
   */
  const [contextIds, setContextIds] = useState<string[]>([]);

  /*
    In auto context mode, the context IDS will automatically be updated whenever a new source text is given.
    If false, then the user has to manually select any sentences to use as context.
  */
  const [contextEnabled, setContextEnabled] = useState(false);

  // While the OCR box(es) are open, the settings can not be changed.
  const [ocrBoxesOpen, setOcrBoxesOpen] = useState(false);

  const handleSearchChange = (e: any) => setSearch(e.currentTarget.value);

  const handleContextEnabled = () => setContextEnabled((s) => !s);

  const toggleSideView = () => setIsSideView((s) => !s);

  /**
   * Open/close the OCR box(es).
   */
  const handleOpenBoxClick = useCallback(() => {
    setOcrBoxesOpen((o) => !o);
    MainGateway.createOcrBox();
  }, []);

  /**
   * Download the backlog into a text file.
   */
  const handleDownloadClick = async () => {
    const w = window as any;
    if (texts.length === 0) return;

    const csvRows = texts.map((t) => [t.sourceText, t.targetText]);
    await w.electronAPI.saveCsvFile(csvRows, ["SourceText", "TargetText"]);
  };

  const pushContext = useCallback(
    (uuid: string) => {
      // Adds to context but limits it such that there is only ever up to 3 auto pushed context sentences.
      // Note that the user can manually have more context sentences, but that is buggy and may crash the model.

      if (contextIds.length >= 3) {
        setContextIds((c) => [...c.slice(1), uuid]);
      } else {
        setContextIds((c) => [...c, uuid]);
      }
    },
    [contextIds]
  );

  const transformInput = () => {
    const contextSourceTexts = texts
      .filter((t) => contextIds.indexOf(t.uuid) > -1)
      .map((t) => t.sourceText);
    const curSourceText = inputText;

    const joined = pTransformerJoin([...contextSourceTexts, curSourceText]);
    return joined;
  };

  const doneTranslatingOne = useCallback(
    async (sourceText: string | null, targetText: string | null) => {
      if (!sourceText || !targetText) return;

      const split = sourceText.split(/<SEP>/);
      const lastSource = split[split.length - 1].trim();

      // Add to texts.
      const newId = uuidv4();

      const w = window as any;
      w.electronAPI.addToTextHistory([targetText], [lastSource], [newId]);

      if (contextEnabled) pushContext(newId);
    },
    [pushContext, contextEnabled]
  );

  const doneTranslatingAll = useCallback(async () => {
    setLoading(false);
  }, []);

  const startTranslating = useCallback(() => {
    setLoading(true);
  }, []);

  /**
   * Submit text to the backend for translating, and receive the end result via websockets.
   */
  const handleProcessTextClick = async () => {
    if (loading) return;

    // Combine inputText with the context.
    const inp = transformInput();

    setInputText("");

    startTranslating(); // Ensure the client is loading.
    await pollTranslateTextStatus(
      () => {},
      doneTranslatingOne,
      doneTranslatingAll
    ); // Create a websocket to listen to the server for progress and the end result.

    // Now we actually begin the translation job on the server.
    await translateText(inp, null, null);
  };

  const handleProcessTextEnter = async (e: any) => {
    if (e.key === "Enter") {
      if (loading) return;
      e.preventDefault();

      await handleProcessTextClick();
    }
  };

  const handleInputChange = (e: any) => setInputText(e.currentTarget.value);

  /**
   * Filter texts such that only texts matching the search criteria are shown.
   */
  const filterTexts = (t: IHistoryText[]) =>
    t.filter(
      (t) =>
        search.length === 0 ||
        t.sourceText.indexOf(search) > -1 ||
        t.targetText[0].toLowerCase().indexOf(search.toLowerCase()) > -1 // I can't remember why but targetTexts is an array of length 1 rather than a string.
    );

  /**
   * Clear the backlog.
   */
  const handleClearClick = async () => {
    const w = window as any;
    if (texts.length === 0) return;

    await w.electronAPI.clearTextHistory();

    setTexts([]);
  };

  /**
   * When initially loaded, retrieve the backlog from the electron backend.
   */
  useEffect(() => {
    let cancel = false;

    const asyncCb = async () => {
      const w = window as any;

      const newTexts = await w.electronAPI.retrieveTextHistory();

      if (!cancel) setTexts(newTexts);
    };

    asyncCb();

    return () => {
      cancel = true;
    };
  }, []);

  const addContext = (uuid: string) => {
    if (contextIds.indexOf(uuid) > -1) {
      setContextIds((s) => s.filter((x) => x !== uuid));
    } else {
      if (contextIds.length >= 6) {
        setContextIds((s) => [...s.slice(1), uuid]);
      } else {
        setContextIds((s) => [...s, uuid]);
      }
    }
  };

  // Listen to history updates from e.g: the OCR box.
  useEffect(() => {
    const w = window as any;

    const cb = (e: any, texts: IHistoryText[]) => {
      if (texts && texts.length > 0) setTexts(texts);
    };
    const removeCb = w.electronAPI.listenTextHistoryUpdate(cb);

    return () => {
      removeCb();
    };
  }, []);

  // If the "auto open OCR window" feature is on, automatically open that window on start.
  useEffect(() => {
    let canceled = false;

    const asyncCb = async () => {
      const data = await MainGateway.getStoreData();

      if (!canceled && data.autoOpenOcrWindow) handleOpenBoxClick();
    };

    asyncCb();

    return () => {
      canceled = true;
    };
  }, [handleOpenBoxClick]);

  // Subcomponents
  const controlsPane = (
    <Stack direction="row" spacing={1}>
      <Tooltip title="Open OCR">
        <Paper sx={{ backgroundColor: "primary.700" }}>
          <IconButton onClick={handleOpenBoxClick} sx={{ borderRadius: 0 }}>
            <MonitorIcon />
          </IconButton>
        </Paper>
      </Tooltip>
      <Tooltip title="OCR Settings">
        <Paper
          elevation={2}
          sx={{
            marginRight: "auto !important",
            backgroundColor: "secondary.700",
          }}
        >
          <IconButton onClick={onOpenOcrSettings} sx={{ borderRadius: 0 }}>
            <SettingsIcon />
          </IconButton>
        </Paper>
      </Tooltip>
      <Tooltip title="Download Translated Backlog">
        <Paper elevation={2}>
          <IconButton
            onClick={handleDownloadClick}
            disabled={texts.length === 0}
            sx={{ borderRadius: 0 }}
          >
            <DownloadIcon />
          </IconButton>
        </Paper>
      </Tooltip>
      <Tooltip title="Clear Backlog">
        <Paper elevation={2}>
          <IconButton
            onClick={handleClearClick}
            disabled={texts.length === 0}
            sx={{ borderRadius: 0 }}
          >
            <RefreshIcon />
          </IconButton>
        </Paper>
      </Tooltip>
      <Tooltip
        title={contextEnabled ? "Disable Context Push" : "Enable Context Push"}
      >
        <Paper elevation={2}>
          <IconButton onClick={handleContextEnabled} sx={{ borderRadius: 0 }}>
            <AutoStoriesIcon />
          </IconButton>
        </Paper>
      </Tooltip>
      <Tooltip title={isSideView ? "Vertical Mode" : "Horizontal Mode"}>
        <Paper elevation={2}>
          <IconButton onClick={toggleSideView} sx={{ borderRadius: 0 }}>
            <OpenInFullIcon />
          </IconButton>
        </Paper>
      </Tooltip>
    </Stack>
  );

  // debugListeners();

  // Main render process
  if (isSideView) {
    return (
      <BaseView>
        <Grid container rowSpacing={0} columnSpacing={2}>
          <Grid item xs={12}>
            {controlsPane}
          </Grid>
          <Grid item xs={6}>
            <Paper className="fullWidth" elevation={2}>
              <TextField
                label="Output"
                size="small"
                placeholder="Target text will appear here."
                multiline
                rows={15}
                value={
                  texts.length === 0 ? "" : texts[texts.length - 1].targetText
                }
              />
            </Paper>
          </Grid>
          <Grid item xs={6}>
            <Paper className="fullWidth" elevation={2}>
              <TextField
                label="Input"
                size="small"
                placeholder="Enter text here..."
                value={inputText}
                onChange={handleInputChange}
                multiline
                rows={15}
                onKeyDown={handleProcessTextEnter}
              />
            </Paper>
          </Grid>
        </Grid>
      </BaseView>
    );
  } else
    return (
      <BaseView>
        <Stack spacing={2} alignContent="space-between" sx={{ width: "100%" }}>
          <Paper className="fullWidth" elevation={2}>
            <TextField
              label="Search"
              size="small"
              value={search}
              onChange={handleSearchChange}
            />
          </Paper>
          <HistoryPane
            texts={filterTexts(texts).map((t) => ({
              ...t,
              sourceText: t.sourceText.replace("<TSOS>", "").trim(),
            }))}
            selectedIds={contextIds}
            onSelectItem={addContext}
          />
          <Stack spacing={1}>
            {controlsPane}
            <Paper className="fullWidth" elevation={2}>
              <TextField
                label="Input"
                size="small"
                placeholder="Type text here... Using Textractor instead? Click the purple button above!"
                value={inputText}
                onChange={handleInputChange}
                onKeyDown={handleProcessTextEnter}
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={handleProcessTextClick}
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
            </Paper>
          </Stack>
        </Stack>
      </BaseView>
    );
};

export default TextView;
