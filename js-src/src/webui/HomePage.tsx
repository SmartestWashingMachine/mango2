import {
  Button,
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
import React, { useState, useEffect } from "react";
import usePagination from "./usePagination";

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

// Yes it's not very secure, you can just see it in the source code.. But if you can see this comment then you're probably not him...
const PASS_CODE = "not4u";

const HomePage = () => {
  const theme = useTheme();
  const matchDownMd = useMediaQuery(theme.breakpoints.down("sm"));

  const [didLogin, setDidLogin] = useState(false);
  const [passcode, setPasscode] = useState("");

  const [search, setSearch] = useState("");

  const [visListPage, trueListPage, flipListPage, onChangeListPage] =
    usePagination();

  const [selFolder, setSelFolder] = useState<string | null>(null);
  // A map where each key is the name of a folder and the values are all of the non .amg files in that folder.
  const [folderMap, setFolderMap] = useState<Record<string, string[]>>({});
  // Date for each folder in folderMap.
  const [folderDates, setFolderDates] = useState<Record<string, number>>({});

  // Current selected image IDX.
  const [visCurIdx, trueCurIdx, flipCurIdx, onChangeCurIdx] = usePagination();

  const [showImageOptions, setShowImageOptions] = useState(true);

  const curFolder =
    selFolder && selFolder in folderMap ? folderMap[selFolder] : null;

  const maxCurIdx = curFolder?.length || 1;

  const nextImage = () => {
    const didSucceed = flipCurIdx(trueCurIdx + 1, false, maxCurIdx);
    if (didSucceed) changeSearchParams(selFolder, trueCurIdx + 1);
  };

  const prevImage = () => {
    const didSucceed = flipCurIdx(trueCurIdx - 1, false, maxCurIdx);
    if (didSucceed) changeSearchParams(selFolder, trueCurIdx - 1);
  };

  // Called once on page load. For listing all data.
  useEffect(() => {
    if (didLogin) {
      let canceled = false;

      const asyncCb = async () => {
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
        if (canceled) return;
        setFolderMap(data.folderMap);
        setFolderDates(data.folderDates);
      };

      asyncCb();

      return () => {
        canceled = true;
      };
    }
  }, [didLogin]);

  // Called once on page load. For new tabs.
  useEffect(() => {
    if (didLogin && Object.keys(folderMap).length > 0) {
      let canceled = false;

      const params = new URLSearchParams(window.location.search);
      const routeFolder = params.get("r");
      const routeCurIdx = params.get("i");

      if (routeFolder && routeCurIdx && !canceled) {
        setSelFolder(routeFolder);
        // We assume the index is within max bounds here.
        flipCurIdx(parseInt(routeCurIdx, 10), false, 1000);
      }

      return () => {
        canceled = true;
      };
    }
  }, [didLogin, folderMap]);

  const selectFolder = (f: string) => {
    flipCurIdx(0, false, maxCurIdx);

    setShowImageOptions(true);
    setSelFolder(f);
    changeSearchParams(f);
  };

  const authenticate = () => {
    if (passcode === PASS_CODE) {
      setDidLogin(true);
      localStorage.setItem("passcode", passcode);
    }
  };

  useEffect(() => {
    const stored = localStorage.getItem("passcode");
    if (stored === PASS_CODE) setDidLogin(true);
  }, []);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [visListPage]);

  const NUM_COLS = matchDownMd ? 2 : 4;
  const ROW_HEIGHT = matchDownMd ? 150 : 300;
  const ROW_GAP = matchDownMd ? 32 : 64;

  if (!didLogin) {
    return (
      <Stack
        spacing={2}
        sx={{ padding: 4, height: "100vh", justifyContent: "center" }}
      >
        <TextField
          onChange={(e: any) => setPasscode(e.currentTarget.value)}
          value={passcode}
          variant="filled"
          label="Passcode"
        />
        <Button color="primary" onClick={authenticate}>
          Login
        </Button>
      </Stack>
    );
  }

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
              href={`?r=${f}&i=0`}
              component="a"
            >
              <img
                src={`${API_URL}/webui/resources/${f}/${folderMap[f][0]}`}
                style={{}}
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

  // For non-infinite
  const imgSrc = getImagePath(trueCurIdx);

  const isInfinite = true;

  // Selected image view:

  return (
    <Stack spacing={2} sx={{ padding: 0, overflowY: "hidden !important" }}>
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
          {!isInfinite && (
            <>
              <TextField
                onChange={(e: any) => onChangeCurIdx(e, maxCurIdx)}
                value={visCurIdx}
                variant="standard"
                sx={{ width: "100px !important" }}
              />
              <Typography
                variant="body2"
                sx={{ marginLeft: 4, marginRight: 2 }}
              >
                of {maxCurIdx}
              </Typography>
            </>
          )}
        </div>
      </Fade>
      {isInfinite ? (
        Array.from(new Array(maxCurIdx), (_, idx) => (
          <img
            src={getImagePath(idx) || undefined}
            className="imageInnerInfinite"
            loading="lazy"
            key={`${idx}img`}
          />
        ))
      ) : (
        <div
          className={
            showImageOptions ? "imageContainer" : "imageContainerExpanded"
          }
        >
          {imgSrc && <img src={imgSrc} className="imageInner" />}
          <div className="imageLeft" onClick={prevImage}></div>
          <div
            className="imageMiddle"
            onClick={() => setShowImageOptions((s) => !s)}
          ></div>
          <div className="imageRight" onClick={nextImage}></div>
        </div>
      )}
    </Stack>
  );
};

export default HomePage;
