import {
  Button,
  CircularProgress,
  Collapse,
  Fade,
  ImageList,
  ImageListItem,
  ImageListItemBar,
  Pagination,
  Stack,
  TextField,
  Typography,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import React, { useState, useEffect, useCallback } from "react";
import usePagination from "./usePagination";
import { useAlerts } from "../components/AlertProvider";
import { v4 as uuidv4 } from "uuid";

// Yeah, this is messy. It's just for development purposes though.

const ITEMS_PER_PAGE = 20;

const paginateItems = <T,>(items: T[], page: number) => {
  const skip = page * ITEMS_PER_PAGE;

  if (skip < items.length)
    return items.slice(skip, Math.min(items.length, skip + ITEMS_PER_PAGE));

  return [];
};

const changeSearchParams = (selFolder: string | null, curIdx: number = 0) => {
  const params = new URLSearchParams(window.location.search);
  if (selFolder === null) {
    params.delete("r");
    params.delete("i");
  } else {
    params.set("r", selFolder);
    params.set("i", `${curIdx}`);
  }

  const query = window.location.pathname + "?" + params.toString();
  history.pushState(null, "", query);
};

const API_URL = "";

const HomePage = () => {
  const pushAlert = useAlerts();
  const theme = useTheme();
  const matchDownMd = useMediaQuery(theme.breakpoints.down("sm"));

  const [search, setSearch] = useState("");

  const [visListPage, trueListPage, flipListPage, onChangeListPage] =
    usePagination();

  const [selFolder, setSelFolder] = useState<string | null>(null);
  // A map where each key is the name of a folder and the values are all of the non .amg files in that folder.
  const [folderMap, setFolderMap] = useState<Record<string, string[]>>({});
  // Date for each folder in folderMap.
  const [folderDates, setFolderDates] = useState<Record<string, number>>({});

  const [showImageOptions, setShowImageOptions] = useState(true);

  const [pendingTasks, setPendingTasks] = useState<string[]>([]);

  const curFolder =
    selFolder && selFolder in folderMap ? folderMap[selFolder] : null;

  const maxCurIdx = curFolder?.length || 1;

  // For the "base" list view.
  const retrieveListOfImages = useCallback(async () => {
    const output = await fetch(`${API_URL}/webui/list`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
    });
    if (output.status !== 200) throw Error("Invalid status code.");

    const data = await output.json();
    if (!data || !data.folderMap) throw Error("Invalid data.");

    return {
      newFolderMap: data.folderMap,
      newFolderDates: data.folderDates,
    };
  }, []);

  // For new tabs.
  const retrieveImagesFromRouteParams = useCallback((folderMapToUse: any) => {
    if (Object.keys(folderMapToUse).length > 0) {
      const params = new URLSearchParams(window.location.search);
      const routeFolder = params.get("r");

      return routeFolder;
    }
  }, []);

  // Called once on page load. For listing all data.
  useEffect(() => {
    let canceled = false;

    const asyncCb = async () => {
      const { newFolderMap, newFolderDates } = await retrieveListOfImages();
      const newSelFolder = retrieveImagesFromRouteParams(newFolderMap);

      if (!canceled) {
        setFolderMap(newFolderMap);
        setFolderDates(newFolderDates);
        if (newSelFolder) setSelFolder(newSelFolder);
      }
    };

    asyncCb();

    return () => {
      canceled = true;
    };
  }, [retrieveImagesFromRouteParams, retrieveListOfImages]);

  const selectFolder = (f: string) => {
    setShowImageOptions(true);
    setSelFolder(f);
    changeSearchParams(f);
  };

  // Scroll on new list page.
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [visListPage]);

  const handleZipUpload = async (e: any) => {
    const formData = new FormData() as any;

    if (!e.target.files || e.target.files.length === 0) return;

    for (const foundFile of e.target.files) {
      let correctedFile: any = null;
      if (
        foundFile.name.endsWith(".zip") &&
        foundFile.type !== "application/zip"
      ) {
        correctedFile = new File([foundFile], foundFile.name, {
          type: "application/zip",
          lastModified: foundFile.lastModified,
        });
      } else {
        correctedFile = foundFile;
      }

      console.log(`Found file: ${correctedFile.name} (${correctedFile.type})`);
      formData.append("file", correctedFile);
    }

    pushAlert("Processing files...");

    let LOGIC_API_URL = window.location.protocol;
    if (LOGIC_API_URL.includes("http")) LOGIC_API_URL = LOGIC_API_URL + "//";
    LOGIC_API_URL += window.location.hostname + ":5000";

    const taskId = uuidv4();
    setPendingTasks((t) => [...t, taskId]);

    const output = await fetch(`${LOGIC_API_URL}/webui/processziptask1`, {
      method: "POST",
      body: formData,
      mode: "no-cors",
      headers: {
        Accept: "application/json",
      },
    });

    setPendingTasks((t) => t.filter((itm) => itm !== taskId));
  };

  const NUM_COLS = matchDownMd ? 2 : 4;
  const ROW_HEIGHT = matchDownMd ? 150 : 300;
  const ROW_GAP = matchDownMd ? 32 : 64;

  // List library view.
  if (!selFolder) {
    const folKeys = Object.keys(folderMap);

    folKeys.sort((a, b) => (folderDates[b] || 0) - (folderDates[a] || 0));

    const filteredItems = folKeys.filter((f) =>
      f.toLowerCase().includes(search.toLowerCase().trim())
    );

    const maxListPage = Math.ceil(folKeys.length / ITEMS_PER_PAGE);

    return (
      <Stack
        spacing={2}
        sx={{ padding: 4, alignContent: "center", alignItems: "center" }}
      >
        <div className="searchOptions">
          <Button
            href="?media=video"
            variant="text"
            color="info"
            sx={{ marginRight: 16 }}
          >
            Videos
          </Button>
          <TextField
            placeholder="Search"
            variant="standard"
            onChange={(e: any) => setSearch(e.currentTarget.value)}
            value={search}
            fullWidth
            sx={{ paddingRight: "8px" }}
          />
          <TextField
            onChange={(e: any) => onChangeListPage(e, maxListPage)}
            value={visListPage}
            placeholder="Page"
            variant="standard"
          />
        </div>
        <Button variant="outlined" color="primary" component="label" fullWidth>
          Translate Images
          <input
            type="file"
            multiple
            onChange={handleZipUpload}
            style={{ display: "none" }}
            accept="application/zip,application/x-zip,application/x-zip-compressed,application/octet-stream"
          />
        </Button>
        <Collapse
          mountOnEnter
          unmountOnExit
          in={pendingTasks.length > 0}
          timeout={500}
        >
          <Stack direction="row" spacing={2}>
            <CircularProgress size={16} color="info" />
            <Typography variant="body2" sx={{ color: "lightgray !important" }}>
              Translating batch... ({pendingTasks.length} remaining)
            </Typography>
          </Stack>
        </Collapse>
        <ImageList
          sx={{
            width: "100%",
            overflowY: "visible !important",
            "& .MuiImageListItem-img": { height: "100% !important" },
          }}
          cols={NUM_COLS}
          rowHeight={ROW_HEIGHT}
          gap={ROW_GAP}
        >
          {paginateItems(filteredItems, trueListPage).map((f) => (
            <ImageListItem
              key={f}
              onClick={(e: any) => {
                e.preventDefault();
                selectFolder(f);
              }}
              href={`?r=${f}`}
              component="a"
            >
              <img
                src={`${API_URL}/webui/resources/${f}/${folderMap[f][0]}`}
                style={{}}
                loading="lazy"
              />
              <ImageListItemBar title={f} />
            </ImageListItem>
          ))}
        </ImageList>
        <Pagination
          count={maxListPage}
          page={parseInt(visListPage as string, 10) || 1}
          onChange={(e, p) => flipListPage(p, true, maxListPage)}
        />
      </Stack>
    );
  }

  // For infinite
  const getImagePath = (idxToUse: number) =>
    curFolder && curFolder.length > idxToUse
      ? `${API_URL}/webui/resources/${selFolder}/${curFolder[idxToUse]}`
      : null;

  // Selected image view:

  return (
    <Stack
      spacing={2}
      sx={{ padding: 0, overflowY: "hidden !important", marginBottom: "4px" }}
    >
      <Fade
        mountOnEnter
        unmountOnExit
        in={showImageOptions}
        style={{ transitionDelay: showImageOptions ? "200ms" : "0ms" }}
        timeout={200}
      >
        <div className="imageOptions">
          <Button
            href="?"
            variant="text"
            color="info"
            onClick={(e: any) => {
              e.preventDefault();
              setSelFolder(null);
              changeSearchParams(null);
            }}
          >
            Back
          </Button>
        </div>
      </Fade>
      <div className="imageInnerInfiniteContainer">
        {Array.from(new Array(maxCurIdx), (_, idx) => (
          <img
            src={getImagePath(idx) || undefined}
            className="imageInnerInfinite"
            loading="lazy"
            key={`${idx}img`}
          />
        ))}
      </div>
    </Stack>
  );
};

export default HomePage;
