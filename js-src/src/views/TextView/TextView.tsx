import React, { useCallback, useEffect, useRef, useState } from "react";
import BaseView from "../BaseView";
import TextField from "@mui/material/TextField";
import {
  Collapse,
  Grid,
  IconButton,
  Paper,
  Stack,
  Tooltip,
  Typography,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import ArrowCircleRightIcon from "@mui/icons-material/ArrowRight";
import HistoryPane from "./components/HistoryPane";
import IHistoryText from "../../types/HistoryText";
import { v4 as uuidv4 } from "uuid";
import DownloadIcon from "@mui/icons-material/Download";
import {
  pollGenericTranslateStatus,
  pollTranslateTextStatus,
  translateText,
} from "../../flaskcomms/textViewComms";
import InputAdornment from "@mui/material/InputAdornment";
import MonitorIcon from "@mui/icons-material/Monitor";
import RefreshIcon from "@mui/icons-material/Refresh";
import SettingsIcon from "@mui/icons-material/SettingsOutlined";
import OpenInFullIcon from "@mui/icons-material/OpenInFull";
import AutoStoriesIcon from "@mui/icons-material/AutoStories";
import ReorderIcon from "@mui/icons-material/Reorder";
import { useLoader } from "../../components/LoaderContext";
import { pTransformerJoin } from "../../utils/pTransformerJoin";
import { debugListeners } from "../../flaskcomms/debugListeners";
import { MainGateway } from "../../utils/mainGateway";
import { useAlerts } from "../../components/AlertProvider";
import { useInterval } from "../..//utils/useInterval";
import ContentPasteIcon from "@mui/icons-material/ContentPaste";

const SPLIT_AND_QUEUES = [/(?=「)/, "　"];

const NEW_LINE_SPLITS = [/\r\n|\r|\n/g];

type TextViewProps = {
  onOpenOcrSettings: () => void;
};

const TextView = ({ onOpenOcrSettings }: TextViewProps) => {
  const theme = useTheme();
  const matchDownMd = useMediaQuery(theme.breakpoints.down("sm"));

  const pushAlert = useAlerts();

  // Retrieved from store. Used when pushing context automatically or from text splitting.
  const [maxContextAmount, setMaxContextAmount] = useState(0);

  // Side view mode is more user-friendly for big text, or users who don't care for the backlog.
  const [isSideView, setIsSideView] = useState(false);

  const [texts, setTexts] = useState<IHistoryText[]>([]);

  const { loading, setLoading, disabled, setDisabled } = useLoader();

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

  // Users can make the history list smaller for easier navigation.
  const [briefHistory, setBriefHistory] = useState(false);

  // Users can hide the buttons and input field at the bottom if they're simply listening to calls to the /translate endpoint.
  const [showingControls, setShowingControls] = useState(true);

  const prevClipboardRef = useRef<string | null>();
  const [readClipboardDelay, setReadClipboardDelay] = useState<number | null>(
    null
  );

  // Just for informative purposes. The actual window capturing logic is in the backend task3 routes file.
  const [captureWindow, setCaptureWindow] = useState("");

  const handleToggleClipboardReading = () =>
    setReadClipboardDelay((d) => (d === null ? 250 : null));

  const handleSearchChange = (e: any) => setSearch(e.currentTarget.value);

  const handleContextEnabled = () => setContextEnabled((s) => !s);

  const toggleSideView = () => setIsSideView((s) => !s);

  /**
   * Open/close the OCR box(es).
   */
  const handleOpenBoxClick = useCallback(() => {
    MainGateway.createOcrBox();

    // Disable other actions (like navigating to other views) when the detached boxes are open.
    setDisabled((d: boolean) => !d);
  }, []);

  /**
   * Download the backlog into a text file.
   */
  const handleDownloadClick = async () => {
    const w = window as any;
    if (texts.length === 0) return;

    const csvRows = texts.map((t) => [t.sourceText, t.targetText]);
    await w.electronAPI.saveCsvFile(csvRows, ["SourceText", "TargetText"]);

    pushAlert("Saved in documents.");
  };

  const pushContext = useCallback(
    (uuid: string) => {
      // Adds to context but limits it such that there is only ever up to N auto pushed context sentences.
      // Note that the user can manually have more context sentences, but that is buggy and may crash the model.

      if (contextIds.length > maxContextAmount) {
        setContextIds((c) => [...c.slice(1), uuid]);
      } else {
        setContextIds((c) => [...c, uuid]);
      }
    },
    [contextIds, maxContextAmount]
  );

  const transformInput = useCallback(
    (curSourceText: string) => {
      const contextSourceTexts = texts
        .filter((t) => contextIds.indexOf(t.uuid) > -1)
        .map((t) => t.sourceText);

      const joined = pTransformerJoin([...contextSourceTexts, curSourceText]);
      return joined;
    },
    [contextIds, texts]
  );

  const doneTranslatingOne = useCallback(
    async (sourceText: string | null, targetText: string | null) => {
      if (!sourceText || !targetText) return;

      const split = sourceText.split(/<SEP>|<TSOS>/);
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

  const processOneText = (inp: string) => {
    return new Promise(async (resolve) => {
      // Create a websocket to listen to the server for progress and the end result.
      await pollTranslateTextStatus(
        () => {},
        doneTranslatingOne,
        () => {
          resolve(null);

          doneTranslatingAll();
        }
      );

      // Now we actually begin the translation job on the server.
      await translateText(inp, null, null);
    });
  };

  // Used for handleProcessTextClick.
  const splitByChar = (textToSplitOn: string, char: any) => {
    return textToSplitOn
      .split(char)
      .map((x) => x.trim())
      .filter((x) => x.length > 0);
  };

  /**
   * Submit text to the backend for translating, and receive the end result via websockets.
   */
  const handleProcessTextClick = async (
    textToUse?: string,
    splitBy?: any[]
  ) => {
    if (loading) return;

    const curSourceText = textToUse || inputText;
    if (!textToUse) {
      setInputText("");
    }

    let allInps = [curSourceText];

    if (splitBy && splitBy.length > 0 && curSourceText.length > 4) {
      // Find the first split character that matters.
      for (const char of splitBy) {
        allInps = splitByChar(curSourceText, char);
        if (allInps.length > 1) break;
      }
    }

    // NOTE: This ignores the settings and always uses up to 3 context TODO
    let ctxQueue: string[] = [];

    for (const curInputText of allInps) {
      if (curInputText.trim().length === 0) continue;

      // Combine curInputText with the context.
      let inp = "";

      if (contextIds.length > 0) {
        // NOTE: Due to react async shenanigans, context will not be applied here (it uses whatever is known for the "first text")
        inp = transformInput(curInputText);
      } else {
        // But in this case (no context pushing and no prior human selected context), contexts will be used within this chunk of text.
        // This is the ideal case when splitting (such as when pasting a large block of text from a novel, separated by newlines).
        inp = pTransformerJoin([...ctxQueue, curInputText]);

        // Add to queue.
        ctxQueue.push(curInputText);
        // ... But keep the queue bounded in length.
        if (ctxQueue.length > maxContextAmount) ctxQueue = ctxQueue.slice(1);
      }

      startTranslating(); // Ensure the client is loading.

      // Create a websocket to listen to the server for progress and the end result.
      // Also process the given inp.
      // Resolve when the text is done.
      await processOneText(inp);
    }
  };

  const handleProcessTextEnter = async (e: any) => {
    if (e.key === "Enter") {
      if (loading) return;
      e.preventDefault();

      await handleProcessTextClick(undefined, NEW_LINE_SPLITS);
    }
  };

  // If the "Read From Clipboard" mode is on (delay is non-null), then automatically translate the clipboard every now and then.
  // Unlike the one from the OCR box, this one is special as it splits long paragraphs (see SPLIT_AND_QUEUES above).
  useInterval(async () => {
    const clipboard = await MainGateway.readClipboard();

    if (prevClipboardRef.current === clipboard) return;
    prevClipboardRef.current = clipboard;

    await handleProcessTextClick(clipboard, SPLIT_AND_QUEUES);
  }, readClipboardDelay);

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
      if (contextIds.length > maxContextAmount) {
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
  // Also initialize a state value from the store state (the max context amount - used for context pushing and auto text splitting).
  // Also use this effect to retrieve the captured window value for visual purposes only (to notify the user that a window is being captured while trying to open detached boxes).
  useEffect(() => {
    let canceled = false;

    const asyncCb = async () => {
      const data = await MainGateway.getStoreData();
      if (canceled) return;

      if (data.autoOpenOcrWindow) handleOpenBoxClick();

      if (!data.contextAmount) return;

      const cAmt = data.contextAmount;
      let newCtxValue = 0;
      if (cAmt === "one") {
        newCtxValue = 1;
      } else if (cAmt === "two") {
        newCtxValue = 2;
      } else if (cAmt === "three") {
        newCtxValue = 3;
      } else if (cAmt === "packed") {
        newCtxValue = 24; // Arbitrary number.
      }

      setMaxContextAmount(newCtxValue);
      setCaptureWindow(data.captureWindow);
    };

    asyncCb();

    return () => {
      canceled = true;
    };
  }, [handleOpenBoxClick]);

  // Poll calls to the /translate endpoint, logging them here (only while the TextView is active though).
  useEffect(() => {
    const cleanup = pollGenericTranslateStatus(
      (genericId, sourceText, targetText) => {
        let lastSource: string = "";
        try {
          const split = sourceText.split(/<SEP>|<TSOS>/);
          lastSource = split[split.length - 1].trim();
        } catch (err) {
          // Only the finalized translation has a sourceText to split on. It's usually empty.
          lastSource = "Loading...";
        }

        const w = window as any;

        w.electronAPI.addToTextHistory(
          [[targetText]], // I forgot why, but we need a nested list here.
          [lastSource],
          [genericId]
        );

        // No context pushing here - the entity sending the translation GET request should handle adding context.
      }
    );

    return () => {
      cleanup();
    };
  }, [doneTranslatingOne]);

  useEffect(() => {
    const cb = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setShowingControls((s) => !s);
        pushAlert("Toggled controls visibility.");
      }
    };

    document.addEventListener("keydown", cb);

    return () => {
      document.removeEventListener("keydown", cb);
    };
  }, [pushAlert]);

  // Subcomponents
  const controlsPane = (
    <Stack direction="row" spacing={1}>
      <Tooltip
        placement="top-end"
        title={
          <>
            <Typography color="inherit" sx={{ fontWeight: "bold" }}>
              {disabled ? "Close" : "Open"} Detached Box{" "}
              {captureWindow.length > 0 && (
                <>
                  <br />
                  <span className="captureWindowLabel">
                    {`(Capturing "${captureWindow}")`}
                  </span>
                </>
              )}
            </Typography>
            <Typography variant="caption" sx={{ color: "hsl(291, 1%, 93%)" }}>
              Detached box(es) can scan the screen or system for text to
              translate and display.
            </Typography>
          </>
        }
      >
        <Paper sx={{ backgroundColor: "primary.700" }}>
          <IconButton onClick={handleOpenBoxClick} sx={{ borderRadius: 0 }}>
            <MonitorIcon />
          </IconButton>
        </Paper>
      </Tooltip>
      <Tooltip title="Detached Box Settings" placement="top-end">
        <Paper
          elevation={2}
          sx={{
            marginRight: "auto !important",
            backgroundColor: "secondary.700",
          }}
        >
          <IconButton
            onClick={onOpenOcrSettings}
            sx={{ borderRadius: 0 }}
            disabled={disabled}
          >
            <SettingsIcon />
          </IconButton>
        </Paper>
      </Tooltip>
      <Tooltip title={briefHistory ? "Expand History" : "Minimize History"}>
        <Paper elevation={2}>
          <IconButton
            onClick={() => setBriefHistory((h) => !h)}
            sx={{ borderRadius: 0 }}
          >
            <ReorderIcon color={briefHistory ? "primary" : undefined} />
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
            <AutoStoriesIcon color={contextEnabled ? "primary" : undefined} />
          </IconButton>
        </Paper>
      </Tooltip>
      <Tooltip
        title={
          <>
            <Typography color="inherit" sx={{ fontWeight: "bold" }}>
              {readClipboardDelay !== null
                ? "Stop Reading From Clipboard"
                : "Read From Clipboard"}
            </Typography>
            <Typography variant="caption" sx={{ color: "hsl(291, 1%, 93%)" }}>
              Automatically translates text as it is copied into the clipboard.
              Newlines, if found, will be used to split the text into separate
              sentences.
            </Typography>
          </>
        }
      >
        <Paper elevation={2}>
          <IconButton
            onClick={handleToggleClipboardReading}
            sx={{ borderRadius: 0 }}
          >
            <ContentPasteIcon
              color={readClipboardDelay !== null ? "primary" : undefined}
            />
          </IconButton>
        </Paper>
      </Tooltip>
      <Tooltip title={isSideView ? "Vertical Mode" : "Horizontal Mode"}>
        <Paper elevation={2}>
          <IconButton onClick={toggleSideView} sx={{ borderRadius: 0 }}>
            <OpenInFullIcon color={isSideView ? "primary" : undefined} />
          </IconButton>
        </Paper>
      </Tooltip>
    </Stack>
  );

  // debugListeners();

  // Main render process
  if (showingControls && isSideView) {
    return (
      <BaseView>
        <Grid container rowSpacing={0} columnSpacing={2}>
          <Grid item xs={12}>
            {controlsPane}
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
            isBrief={briefHistory}
          />
          {showingControls && (
            <Stack spacing={1}>
              {controlsPane}
              <Paper className="fullWidth" elevation={2}>
                <TextField
                  label="Input"
                  size="small"
                  placeholder={
                    matchDownMd
                      ? "Type text here or click the purple button above!"
                      : "Type text here... Using Textractor instead? Click the purple button above!"
                  }
                  value={inputText}
                  multiline
                  maxRows={3}
                  onChange={handleInputChange}
                  onKeyDown={handleProcessTextEnter}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={() => {
                            handleProcessTextClick();
                          }}
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
          )}
        </Stack>
      </BaseView>
    );
};

export default TextView;
