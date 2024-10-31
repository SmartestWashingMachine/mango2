import React, { memo, useCallback, useEffect, useState } from "react";
import BaseView from "../BaseView";
import ImageInput from "./components/ImageViewer/ImageInput";
import ImageViewer from "./components/ImageViewer/ImageViewer";
import FileListPane from "./components/FileListPane";
import FileInfo from "../../types/FileInfo";
import {
  pollTranslateImagesStatus,
  switchCleaningApp,
  switchRedrawingApp,
  switchTileSize,
  translateImages,
} from "../../flaskcomms/imageViewComms";
import { Stack } from "@mui/material";
import ImageViewOptions from "./components/ImageViewer/ImageViewOptions";
import { useLoader } from "../../components/LoaderContext";
import { useAlerts } from "../../components/AlertProvider";
import ImageFolderInputDialog from "./components/ImageFolderInputDialog";
import { useInstalledModelsRetriever } from "../../utils/useInstalledModelsRetriever";
import { v4 as uuidv4 } from "uuid";

const RightPane = memo(
  ({
    handleChangeSelectedPath,
    handleRefresh,
    handleBackClick,
    rootItem,
    selectedPath,
    handleChangeCleaningMode,
    handleChangeRedrawingMode,
    handleChangeTileWidth,
    handleChangeTileHeight,
    cleaningMode,
    redrawingMode,
    installedModels,
    tileWidth,
    tileHeight,
  }: any) => (
    <Stack spacing={2} sx={{ height: "100%" }} key="library-stack">
      <FileListPane
        rootItem={rootItem}
        selectedPath={selectedPath}
        onSelectFileInfo={handleChangeSelectedPath}
        onRefresh={handleRefresh}
        onBackClick={handleBackClick}
      />
      <ImageViewOptions
        redrawingMode={redrawingMode}
        cleaningMode={cleaningMode}
        onChangeCleaningMode={handleChangeCleaningMode}
        onChangeRedrawingMode={handleChangeRedrawingMode}
        tileWidth={tileWidth}
        tileHeight={tileHeight}
        onChangeTileWidth={handleChangeTileWidth}
        onChangeTileHeight={handleChangeTileHeight}
        installedModels={installedModels}
      />
    </Stack>
  )
);

const ImageView = () => {
  const pushAlert = useAlerts();

  const [showingImages, setShowingImages] = useState(false);

  const [selectedPath, setSelectedPath] = useState<string | null>(null);

  const [rootItem, setRootItem] = useState<FileInfo | null>(null);

  const [viewingImagePaths, setViewingImagePaths] = useState<string[]>([]);

  // While loading (processing images in the backend), further uploading will be disabled.
  const { loading, setLoading } = useLoader();
  const [loadingProgress, setLoadingProgress] = useState(0);
  // If loading (processing images in the backend), then this list contains the names of images that have not been completed yet.
  const [pendingImageNames, setPendingImageNames] = useState<string[]>([]);

  const installedModels = useInstalledModelsRetriever();

  const handleChangeSelectedPath = async (f: FileInfo) => {
    setSelectedPath(f.fullPath);

    if (f.childrenItems.length > 0) {
      setViewingImagePaths(
        f.childrenItems
          .filter((c) => c.childrenItems.length === 0)
          .map((c) => c.fullPath)
      );
    } else {
      // Case 2: The selected item is a file (non-folder). Only add the file.
      setViewingImagePaths([f.fullPath]);
    }
    // NOTE: viewingImagePaths must be updated whenever renaming/deleting a file.
  };

  const updateProgress = useCallback((progress: number) => {
    setLoadingProgress(progress);
  }, []);

  const doneTranslatingOne = useCallback(
    async (
      base64Image: string,
      folderName: string,
      fileName: string,
      annotations?: any[]
    ) => {
      if (!base64Image) return;

      const w = window as any;

      const { rootItem, imagePaths, folderPath } =
        await w.electronAPI.saveBase64Files(
          [base64Image],
          folderName,
          fileName,
          annotations
        );

      // Update the rootItem so that the new image file name is displayed on the right pane.
      setRootItem(rootItem);

      // Then update the left pane stuff.
      setViewingImagePaths(imagePaths);
      setSelectedPath(folderPath);

      // Images in the backend are always processed in order, so we can safely remove the first image in the pending list.
      setPendingImageNames((l) => (l.length > 0 ? l.slice(1) : []));
    },
    []
  );

  const doneTranslatingAll = useCallback(async () => {
    // no-op now.
  }, []);

  const startTranslating = useCallback(() => {
    // setLoadingProgress(0);
    setLoading(true);
  }, []);

  // Used when uploading images to be translated.
  const [files, setFiles] = useState<any>(null);
  const [createFolderOpen, setCreateFolderOpen] = useState(false);

  const [cleaningMode, setCleaningMode] = useState("simple");
  const [redrawingMode, setRedrawingMode] = useState("amg_convert");

  const [tileWidth, setTileWidth] = useState(-1);
  const [tileHeight, setTileHeight] = useState(-1);

  const handleCeateFolderNameClose = () => {
    setCreateFolderOpen(false);
  };

  const handleCreateFolderNameDone = useCallback(
    async (folderName: string) => {
      const taskId = uuidv4();

      setCreateFolderOpen(false);

      startTranslating(); // Ensure the client is loading.

      const doneWithOne = (
        base64Image: string,
        fileName: string,
        annotations?: any[]
      ) => {
        doneTranslatingOne(base64Image, folderName, fileName, annotations);

        pushAlert(`Saved "${fileName}".`);
      };

      await pollTranslateImagesStatus(
        updateProgress,
        doneWithOne,
        doneTranslatingAll,
        taskId,
      ); // Create a websocket to listen to the server for progress and the end result.

      // Now we actually begin the translation job on the server.
      const sortedFileNames = await translateImages(files, null, taskId);

      setPendingImageNames(l => [...l, ...sortedFileNames]);
    },
    [
      startTranslating,
      updateProgress,
      doneTranslatingOne,
      doneTranslatingAll,
      pushAlert,
      files, // Hopefully nothing breaks O_O
    ]
  );

  const handleSelectFiles = useCallback(async (newFiles: any) => {
    setFiles(newFiles);

    setCreateFolderOpen(true);
  }, []);

  useEffect(() => {
    const w = window as any;

    let didCancel = false;

    const asyncCb = async () => {
      const rootItem = await w.electronAPI.retrieveFiles();
      if (rootItem && !didCancel) {
        setRootItem(rootItem);
      }

      const imageAddData = await w.electronAPI.retrieveImageAddData();
      switchCleaningApp(imageAddData.cleaningMode);
      switchRedrawingApp(imageAddData.redrawingMode);
      switchTileSize(imageAddData.tileWidth, imageAddData.tileHeight);

      setCleaningMode(imageAddData.cleaningMode);
      setRedrawingMode(imageAddData.redrawingMode);
      setTileWidth(imageAddData.tileWidth);
      setTileHeight(imageAddData.tileHeight);
    };

    asyncCb();

    return () => {
      didCancel = true;
    };
  }, []);

  useEffect(() => {
    if (pendingImageNames.length === 0) {
      setLoading(false);
      setLoadingProgress(0);
    }
  }, [pendingImageNames]);

  const handleRefresh = async () => {
    const w = window as any;

    const rootItem = await w.electronAPI.retrieveFiles();
    if (rootItem) {
      setRootItem(rootItem);
      setViewingImagePaths([]);
      setSelectedPath(null);
    }
  };

  const handleBackClick = () => {
    setSelectedPath(null);
    setViewingImagePaths([]);
  };

  const handleChangeCleaningMode = (m: string) => {
    const w = window as any;
    w.electronAPI.setStoreValue("cleaningMode", m);

    setCleaningMode(m);
    switchCleaningApp(m);
  };

  const handleChangeRedrawingMode = (m: string) => {
    const w = window as any;
    w.electronAPI.setStoreValue("redrawingMode", m);

    setRedrawingMode(m);
    switchRedrawingApp(m);
  };

  const handleChangeTileWidth = (val: number) => {
    const w = window as any;
    w.electronAPI.setStoreValue("tileWidth", val);

    setTileWidth(val);
    switchTileSize(val, tileHeight);
  };

  const handleChangeTileHeight = (val: number) => {
    const w = window as any;
    w.electronAPI.setStoreValue("tileHeight", val);

    setTileHeight(val);
    switchTileSize(tileWidth, val);
  };

  const getFolderFromImage = useCallback((imagePath: string) => {
    // Try and get the folder that the image is in. Not as clean as I'd like it to be. TODO.
    const regex = /(?:\/|\\).+(?:\/|\\)(.+)(?:\/|\\).+\.amg/;

    const matches = imagePath.match(regex);
    if (!matches || matches.length < 2) return;

    return matches[1];
  }, []);

  const handleSaveEditedImage = useCallback(
    async (image: any, imagePath: string) => {
      const w = window as any;

      const pat = getFolderFromImage(imagePath);
      const { rootItem } = await w.electronAPI.saveImage(pat, image);
      setRootItem(rootItem);
      setSelectedPath(null);
      setViewingImagePaths([]);
    },
    [getFolderFromImage]
  );

  const rightPane = (
    <RightPane
      handleChangeSelectedPath={handleChangeSelectedPath}
      handleRefresh={handleRefresh}
      handleBackClick={handleBackClick}
      rootItem={rootItem}
      selectedPath={selectedPath}
      handleChangeCleaningMode={handleChangeCleaningMode}
      handleChangeRedrawingMode={handleChangeRedrawingMode}
      cleaningMode={cleaningMode}
      redrawingMode={redrawingMode}
      installedModels={installedModels}
      tileWidth={tileWidth}
      tileHeight={tileHeight}
      handleChangeTileWidth={handleChangeTileWidth}
      handleChangeTileHeight={handleChangeTileHeight}
    />
  );

  useEffect(() => {
    const cb = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setShowingImages((s) => !s);
        pushAlert("Toggled image pane.");
      }
    };

    document.addEventListener("keydown", cb);

    return () => {
      document.removeEventListener("keydown", cb);
    };
  }, [pushAlert]);

  const leftPane = showingImages ? (
    <div></div>
  ) : viewingImagePaths.length > 0 ? (
    <ImageViewer
      imagePaths={viewingImagePaths}
      onFilesSelected={handleSelectFiles}
      selectDisabled={loading}
      loadingProgress={loadingProgress}
      pendingImageNames={pendingImageNames}
      onSaveEditedImage={handleSaveEditedImage}
      selectedPath={selectedPath}
    />
  ) : (
    <ImageInput
      onFilesSelected={handleSelectFiles}
      selectDisabled={loading}
      loadingProgress={loadingProgress}
      pendingImageNames={pendingImageNames}
    />
  );

  return (
    <BaseView rightPane={rightPane}>
      {leftPane}
      <ImageFolderInputDialog
        open={createFolderOpen}
        onDone={handleCreateFolderNameDone}
        onClose={handleCeateFolderNameClose}
        rootItem={rootItem}
      />
    </BaseView>
  );
};

export default ImageView;
