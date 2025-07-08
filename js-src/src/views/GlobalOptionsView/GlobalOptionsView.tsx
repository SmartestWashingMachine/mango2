import { Button, MenuItem, Stack, TextField, Typography } from "@mui/material";
import React, { useState, useEffect } from "react";
import ReplaceTermsList from "./components/ReplaceTermsList";
import {
  setSeed,
  triggerCircuitBreak,
} from "../../flaskcomms/optionsViewComms";
import IReplaceTerm from "../../types/ReplaceTerm";
import BaseView from "../BaseView";
import { TEXT_DETECTION_OPTIONS } from "../../utils/appOptions/textDetectionOptions";
import { TEXT_LINE_OPTIONS } from "../../utils/appOptions/textLineOptions";
import { TRANSLATION_OPTIONS } from "../../utils/appOptions/translationOptions";
import { RERANKING_OPTIONS } from "../../utils/appOptions/rerankingOptions";
import { SPELLING_CORRECTION_OPTIONS } from "../../utils/appOptions/spellingCorrectionOptions";
import { DECODING_OPTIONS } from "../../utils/appOptions/decodingOptions";
import UpdateNumberField from "../../components/UpdateNumberField";
import UpdateCheckbox from "../../components/UpdateCheckbox";
import UpdateListField from "../../components/UpdateListField";
import { MainGateway } from "../../utils/mainGateway";
import PaginatedTabs from "../../components/PaginatedTabs";
import { OCR_OPTIONS } from "../../utils/appOptions/ocrOptions";
import { getInstalledModels } from "../../flaskcomms/getInstalledModels";
import { useAlerts } from "../../components/AlertProvider";
import { useInstalledModelsRetriever } from "../../utils/useInstalledModelsRetriever";
import GLOBAL_OPTIONS_PARTIAL_PRESETS, {
  PresetItem,
} from "./globalOptionsPartialPresets";
import { previewCaptureWindow } from "../../flaskcomms/previewCaptureWindow";
import { getBoxDisplayName } from "../../utils/getBoxDisplayName";
import DictionaryList from "./components/DictionaryList";
import INameEntry from "../../types/NameEntry";

export type GlobalOptionsViewProps = {
  goOcrOptionsTab: () => void;
};

const GlobalOptionsView = ({ goOcrOptionsTab }: GlobalOptionsViewProps) => {
  const pushAlert = useAlerts();

  const [terms, setTerms] = useState<IReplaceTerm[]>([]);

  const [nameEntries, setNameEntries] = useState<INameEntry[]>([]);

  const [isLoading, setIsLoading] = useState(true);

  const [loadedData, setLoadedData] = useState<any>({});

  const [capturedWindowPreview, setCapturedWindowPreview] = useState("");

  const [curWindowName, setCurWindowName] = useState("");

  const installedModels = useInstalledModelsRetriever();

  useEffect(() => {
    let didCancel = false;

    const asyncCb = async () => {
      const data = await MainGateway.getStoreData();

      if (!didCancel) {
        setLoadedData(data);
        setTerms(data.terms);
        setNameEntries(data.nameEntries);

        setIsLoading(false);
      }
    };

    asyncCb();

    return () => {
      didCancel = true;
    };
  }, []);

  useEffect(() => {
    // Sync terms when one is made or deleted. In the future I should really just get rid of this stupid abstraction between the electron store and the frontend...
    const cb = (e: any, s: any, oldS: any) => {
      //if (s.terms.length !== oldS.terms.length || s.terms.length === 0)
      setTerms(s.terms);
      setNameEntries(s.nameEntries);
    };
    const removeCb = MainGateway.listenStoreDataChange(cb);

    return () => {
      removeCb();
    };
  }, []);

  const setStoreValue = async (key: string, value: any, doResend = true) => {
    await MainGateway.setStoreValue(key, value);

    if (doResend) await MainGateway.resendData();

    setLoadedData((d: any) => ({ ...d, [key]: value }));
  };

  const updateTerm = (
    termUuid: string,
    termKey: keyof IReplaceTerm,
    termValue: string | boolean
  ) => {
    MainGateway.updateTerm(termUuid, termKey, termValue);
  };

  const removeTerm = (termUuid: string) => {
    MainGateway.deleteTerm(termUuid);
  };

  const createTerm = () => {
    MainGateway.newTerm();
  };

  const importTerms = async () => {
    await MainGateway.importTerms();
  };

  const exportTerms = async () => {
    await MainGateway.exportTerms();
  };

  const updateNameEntry = (
    uuid: string,
    k: keyof INameEntry,
    v: string | boolean
  ) => {
    MainGateway.updateNameEntry(uuid, k, v);
  };

  const removeNameEntry = (uuid: string) => {
    MainGateway.deleteNameEntry(uuid);
  };

  const createNameEntry = () => {
    MainGateway.newNameEntry();
  };

  const handleFixSeed = async () => {
    await setSeed(42);
  };

  const handleCircuitBreak = async () => {
    await triggerCircuitBreak();
  };

  const handleOpenModelsFolder = async () => {
    await MainGateway.openModelsFolder();
  };

  const handleOpenFontsFolder = async () => {
    await MainGateway.openFontsFolder();
  };

  const handleOpenLogsFolder = async () => {
    await MainGateway.openLogsFolder();
  };

  const handleOpenCacheFolder = async () => {
    await MainGateway.openCacheFolder();
  };

  const handleResetSettings = async () => {
    await MainGateway.resetSettings();

    const data = await MainGateway.getStoreData();
    setLoadedData(data);

    pushAlert("Settings reset!");
  };

  const itemEnabled = (x: { name: string; value: string; desc: string }) => {
    const allowedItems = [
      "None",
      "MAP Beam Decoding",
      "MBR Sampling",
      "MBR Beam Sampling",
    ];
    if (allowedItems.includes(x.name)) return true;
    return installedModels.indexOf(x.value) !== -1;
  };

  const selectQuickPreset = async (e: any) => {
    const presetName = e.target.value;
    const preset = GLOBAL_OPTIONS_PARTIAL_PRESETS.find(
      (x) => x.name === presetName
    );
    if (!preset) return;

    for (const [key, value] of Object.entries(preset.opts)) {
      if (Array.isArray(value)) {
        // Allow for fallbacks in setting most models.
        for (const potentialModel of value) {
          if (installedModels.indexOf(potentialModel) > -1) {
            await setStoreValue(key, potentialModel, false);
            break;
          }
        }
      } else {
        // Otherwise just set the value normally.
        await setStoreValue(key, value, false);
      }
    }

    await MainGateway.resendData();
  };

  const presetEnabled = (x: any) => {
    const { opts } = x;

    // Look in all the models used by the preset; if the model is not installed it's a no-go.
    return Object.keys(opts).every((k: any) => {
      if (!k.includes("ModelName")) return true;

      // Is a model; test to see if it or any of the fallbacks are in the installed set.
      const arr = opts[k] as string[];
      return arr.some((x) => installedModels.indexOf(x));
    });
  };

  const renderItem = (x: { name: string; value: string; desc: string }) => [
    <MenuItem value={x.value} dense disabled={!itemEnabled(x)}>
      {x.name}
    </MenuItem>,
    <MenuItem disabled value="" divider dense>
      <em
        style={{
          fontSize: "small",
          wordWrap: "break-word",
          whiteSpace: "initial",
        }}
      >
        {x.desc}
      </em>
    </MenuItem>,
  ];

  if (isLoading) return <div></div>;

  const {
    textLineModelName,
    textDetectionModelName,
    textRecognitionModelName,
    translationModelName,
    rerankingModelName,
    spellCorrectionModelName,
    enableCuda,
    forceTranslationCPU,
    forceSpellingCorrectionCPU,
    forceTdCpu,
    forceTlCpu,
    forceOcrCpu,
    contextAmount,
    strokeSize,
    autoOpenOcrWindow,
    decodingMode,
    numBeams,
    numGpuLayersMt,
    topK,
    topP,
    epsilonCutoff,
    lengthPenalty,
    noRepeatNgramSize,
    temperature,
    repetitionPenalty,
    maxLengthA,
    bottomTextOnly,
    batchOcr,
    cutOcrPunct,
    ignoreDetectSingleWords,
    sortTextFromTopLeft,
    useTranslationServer,
    memoryEfficientTasks,
    cacheMt,
    captureWindow,
    boxes,
  } = loadedData;

  const decodingParamsIgnored = decodingMode === "beam";

  const handlePreviewCaptureWindow = async () => {
    await MainGateway.resendData();
    const imageBase64 = await previewCaptureWindow();

    setCapturedWindowPreview(imageBase64);
  };

  const handlePreviewCaptureWindowWithBox = async (b: any) => {
    const coords = [b.xOffset, b.yOffset, b.width, b.height];

    await MainGateway.resendData();
    const imageBase64 = await previewCaptureWindow(coords);
    setCapturedWindowPreview(imageBase64);
  };

  return (
    <BaseView>
      <PaginatedTabs
        headers={
          <>
            <Button
              variant="text"
              onClick={goOcrOptionsTab}
              color={"info"}
              sx={() => ({
                fontWeight: "normal",
                color: "hsl(291, 3%, 74%)",
                marginBottom: 2,
              })}
              size="small"
            >
              Detached Box Settings
            </Button>
          </>
        }
        items={{
          "Quick Presets": {
            "Quick Presets": (
              <TextField
                onChange={selectQuickPreset}
                defaultValue=""
                helperText="You can select a preset here to quickly configure the models used behind the scenes. Some presets will require additional model packs to be installed."
                variant="standard"
                select
              >
                {GLOBAL_OPTIONS_PARTIAL_PRESETS.map((b) => [
                  <MenuItem
                    value={b.name}
                    key={b.name}
                    disabled={!presetEnabled(b)}
                  >
                    {b.name}
                  </MenuItem>,
                  <MenuItem
                    disabled
                    value="disabledvalue"
                    divider
                    dense
                    key={b.description}
                  >
                    <em
                      style={{
                        fontSize: "small",
                        wordWrap: "break-word",
                        whiteSpace: "initial",
                      }}
                    >
                      {b.description}
                    </em>
                  </MenuItem>,
                ])}
              </TextField>
            ),
          },
          Models: {
            "Text Line Model": (
              <UpdateListField
                keyName="textLineModelName"
                changeValue={setStoreValue}
                defaultValue={textLineModelName}
                label="Text Line Model"
                helperText="Can be used when scanning images. May improve accuracy at the cost of speed."
              >
                {TEXT_LINE_OPTIONS.map(renderItem)}
              </UpdateListField>
            ),
            "Text Detection Model": (
              <UpdateListField
                changeValue={setStoreValue}
                keyName="textDetectionModelName"
                defaultValue={textDetectionModelName}
                label="Text Detection Model"
                helperText="Used when scanning images."
              >
                {TEXT_DETECTION_OPTIONS.map(renderItem)}
              </UpdateListField>
            ),
            "Text Recognition Model": (
              <UpdateListField
                changeValue={setStoreValue}
                keyName="textRecognitionModelName"
                defaultValue={textRecognitionModelName}
                label="Text Recognition Model"
                helperText="Used when scanning images."
              >
                {OCR_OPTIONS.map(renderItem)}
              </UpdateListField>
            ),
            "Translation Model": (
              <UpdateListField
                changeValue={setStoreValue}
                keyName="translationModelName"
                defaultValue={translationModelName}
                label="Translation Model"
              >
                {TRANSLATION_OPTIONS.map(renderItem)}
              </UpdateListField>
            ),
            "Reranking Model": (
              <UpdateListField
                changeValue={setStoreValue}
                keyName="rerankingModelName"
                defaultValue={rerankingModelName}
                label="Reranking Model"
                helperText="May improve translation quality. Only works if the decoding mode is NOT set to MAP Beam Decoding."
              >
                {RERANKING_OPTIONS.map(renderItem)}
              </UpdateListField>
            ),
            "Editing Model": (
              <UpdateListField
                changeValue={setStoreValue}
                keyName="spellCorrectionModelName"
                defaultValue={spellCorrectionModelName}
                label="Editing Model"
                helperText="Used to correct translations."
              >
                {SPELLING_CORRECTION_OPTIONS.map(renderItem)}
              </UpdateListField>
            ),
          },
          "General Performance": {
            "Enable CUDA": (
              <UpdateCheckbox
                changeValue={setStoreValue}
                keyName="enableCuda"
                defaultValue={enableCuda}
                tooltip="4 GB VRAM can work if MT model is forced onto the CPU."
                label="Enable CUDA"
                helperText="Will improve speed IF using a good GPU that supports CUDA. 4 GB of VRAM is required to use a non-Gem translation model for text or clipboard translations alone, and 8 GB VRAM is usually required to OCR and translate images on a GPU. But the entire process can be run on 4 GB VRAM if a Gem translation model is used instead. You can also force parts of the process to run on the CPU instead with the options below."
              />
            ),
            "(Gem) Number of GPU Layers to Offload": (
              <UpdateNumberField
                label="(Gem) Number of GPU Layers to Offload"
                changeValue={setStoreValue}
                keyName="numGpuLayersMt"
                defaultValue={numGpuLayersMt}
                helperText="Only works on Gem translation models. The number of layers to offload to the GPU if CUDA is enabled. This is used to reduce the memory usage of the translation model. This can safely be set to 22 if you have 4 GB VRAM. Set to 99 to offload all layers."
                valueType="int"
                safeValue={22}
                minValue={-1}
                maxValue={99}
              />
            ),
            "(Non Gem) Use Efficient Translator": (
              <UpdateCheckbox
                changeValue={setStoreValue}
                keyName="useTranslationServer"
                defaultValue={useTranslationServer}
                label="Use Efficient Translator"
                helperText="Certain translation models will run faster. Requires efficient translation models to be installed."
              />
            ),
            "Memory Efficient Tasks": (
              <UpdateCheckbox
                changeValue={setStoreValue}
                keyName="memoryEfficientTasks"
                defaultValue={memoryEfficientTasks}
                label="Memory Efficient Tasks"
                helperText="Translating images or videos will require much less memory, but the models have to be loaded at the start of every task. This allows you to run a full non-Gem OCR + translation process on a GPU with 4 GB VRAM if 'Use Efficient Translator' is enabled."
              />
            ),
            "Force Text Box on CPU": (
              <UpdateCheckbox
                changeValue={setStoreValue}
                keyName="forceTdCpu"
                defaultValue={forceTdCpu}
                tooltip="Has no effect if CUDA is disabled."
                label="Force Text Box on CPU"
                helperText="The text box detection model will ALWAYS be on the CPU rather than the GPU. Can decrease memory usage at the cost of speed."
              />
            ),
            "Force Text Line on CPU": (
              <UpdateCheckbox
                changeValue={setStoreValue}
                keyName="forceTlCpu"
                defaultValue={forceTlCpu}
                tooltip="Has no effect if CUDA is disabled."
                label="Force Text Line on CPU"
                helperText="The text line detection model will ALWAYS be on the CPU rather than the GPU. Can decrease memory usage at the cost of speed."
              />
            ),
            "Force OCR on CPU": (
              <UpdateCheckbox
                changeValue={setStoreValue}
                keyName="forceOcrCpu"
                defaultValue={forceOcrCpu}
                tooltip="Has no effect if CUDA is disabled."
                label="Force OCR on CPU"
                helperText="The OCR model will ALWAYS be on the CPU rather than the GPU. Can decrease memory usage at the cost of speed."
              />
            ),
            "Force MT on CPU": (
              <UpdateCheckbox
                changeValue={setStoreValue}
                keyName="forceTranslationCPU"
                defaultValue={forceTranslationCPU}
                tooltip="Has no effect if CUDA is disabled."
                label="Force MT on CPU"
                helperText="The translation model will ALWAYS be on the CPU rather than the GPU. Can decrease memory usage at the cost of speed."
              />
            ),
            "Force Editing on CPU": (
              <UpdateCheckbox
                changeValue={setStoreValue}
                keyName="forceSpellingCorrectionCPU"
                defaultValue={forceSpellingCorrectionCPU}
                tooltip="Has no effect if CUDA is disabled."
                label="Force Editing on CPU"
                helperText="The editing model will ALWAYS be on the CPU rather than the GPU. Can decrease memory usage at the cost of speed."
              />
            ),
            "Context Amount": (
              <UpdateListField
                keyName="contextAmount"
                changeValue={setStoreValue}
                defaultValue={contextAmount}
                label="Context Amount"
                helperText="How many prior sentences to use as context for image / game / book translations. Lowering this may improve speed."
              >
                <MenuItem value="zero" dense>
                  Zero
                </MenuItem>
                <MenuItem value="three" dense>
                  Three
                </MenuItem>
                <MenuItem value="two" dense>
                  Two
                </MenuItem>
                <MenuItem value="one" dense>
                  One
                </MenuItem>
                <MenuItem value="packed" dense>
                  As many as possible (DANGEROUS!)
                </MenuItem>
              </UpdateListField>
            ),
            "Redrawing Edge Size": (
              <UpdateNumberField
                label="Redrawing Edge Size"
                changeValue={setStoreValue}
                keyName="strokeSize"
                defaultValue={strokeSize}
                helperText="The size of the text edge when automatically redrawing translated images."
                valueType="float"
                safeValue={0.5}
                minValue={0.1}
                maxValue={150}
              />
            ),
            "Auto Open Detached Box": (
              <UpdateCheckbox
                changeValue={setStoreValue}
                keyName="autoOpenOcrWindow"
                defaultValue={autoOpenOcrWindow}
                helperText="Automatically open the detached box(es) when the Text tab is selected."
                label="Auto Open Detached Box"
              />
            ),
            "Bottom Text Only": (
              <UpdateCheckbox
                changeValue={setStoreValue}
                keyName="bottomTextOnly"
                defaultValue={bottomTextOnly}
                helperText="Only scan the bottom region of the video or images. Can be useful for video translation tasks."
                label="Bottom Text Only"
              />
            ),
            "Batch OCR Lines": (
              <UpdateCheckbox
                changeValue={setStoreValue}
                keyName="batchOcr"
                defaultValue={batchOcr}
                helperText="Batch text lines together for faster OCR processing. Uses more memory."
                label="Batch OCR Lines"
              />
            ),
            "Cut OCR Punctuation": (
              <UpdateCheckbox
                changeValue={setStoreValue}
                keyName="cutOcrPunct"
                defaultValue={cutOcrPunct}
                helperText="Cut off potentially erroneous end-of-line punctuation from OCR'd texts."
                label="Cut OCR Punctuation"
              />
            ),
            "Ignore Single Words In Images": (
              <UpdateCheckbox
                changeValue={setStoreValue}
                keyName="ignoreDetectSingleWords"
                defaultValue={ignoreDetectSingleWords}
                helperText="Removes potentially erroneous single word detections in image translation jobs."
                label="Ignore Single Words In Images"
              />
            ),
            "Sort Texts Left-to-Right": (
              <UpdateCheckbox
                changeValue={setStoreValue}
                keyName="sortTextFromTopLeft"
                defaultValue={sortTextFromTopLeft}
                helperText="When scanning images, texts are assumed to be read from left-to-right instead of right-to-left. This is used to decide how context is added."
                label="Sort Texts Left-to-Right"
              />
            ),
          },
          Regex: {
            Regex: (
              <ReplaceTermsList
                terms={terms}
                updateTerm={updateTerm}
                createTerm={createTerm}
                removeTerm={removeTerm}
                importTerms={importTerms}
                exportTerms={exportTerms}
              />
            ),
          },
          Dictionary: {
            Dictionary: (
              <DictionaryList
                entries={nameEntries}
                updateEntry={updateNameEntry}
                createEntry={createNameEntry}
                removeEntry={removeNameEntry}
              />
            ),
          },
          "Import Files": {
            "Open Models Folder": (
              <>
                <Button
                  sx={{
                    mt: 8,
                    fontWeight: "normal",
                    color: "white !important",
                    backgroundColor: "primary.600",
                  }}
                  variant="contained"
                  fullWidth
                  onClick={handleOpenModelsFolder}
                >
                  Open Models Folder
                </Button>
                <Typography variant="caption" color="info">
                  Additional models can be installed in this folder.
                </Typography>
              </>
            ),
            "Cache Translations": (
              <UpdateCheckbox
                changeValue={setStoreValue}
                keyName="cacheMt"
                defaultValue={cacheMt}
                helperText={`Translations will be cached. You can also share the cache files with other users, allowing for near "instant" translations as they OCR text in games or other media.`}
                label="Cache Translations"
              />
            ),
            "Open Translation Cache Folder": (
              <>
                <Button
                  sx={{
                    mt: 8,
                    fontWeight: "normal",
                    color: "white !important",
                    backgroundColor: "primary.600",
                  }}
                  variant="contained"
                  fullWidth
                  onClick={handleOpenCacheFolder}
                >
                  Open Translation Cache Folder
                </Button>
                <Typography variant="caption" color="info">
                  All translations are cached in the index and machine
                  translations files. You can clear the cache or share it with
                  other users, allowing for near "instant" translations as they
                  OCR text in games or other media.
                </Typography>
              </>
            ),
            "Open Fonts Folder": (
              <>
                <Button
                  sx={{ mt: 8 }}
                  variant="outlined"
                  color="secondary"
                  fullWidth
                  onClick={handleOpenFontsFolder}
                >
                  Open Fonts Folder
                </Button>
                <Typography variant="caption" color="info">
                  Font files can be placed in the folder for image editing
                  purposes, or to change the font used by the OCR / text box.
                </Typography>
              </>
            ),
          },
          "Capture Specific Window": {
            "Capture Specific Window": (
              <Typography align="center" variant="body2">
                When you OCR a game with multiple detached boxes, you may want
                to overlap some boxes without them OCR'ing each other. If a
                window partially matching this name is found, only the contents
                of that window can be OCR'd.{" "}
                <b>Make sure the window is visible somewhere on the screen.</b>
              </Typography>
            ),
            "Specific Window": (
              <div className="specificWindowContainer">
                <img
                  src={
                    capturedWindowPreview.length > 0
                      ? `data:image/png;base64,${capturedWindowPreview}`
                      : "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" // Just an empty 1x1 GIF.
                  }
                  className="specificWindowInner"
                />
              </div>
            ),
            "Window Name": (
              <TextField
                label="Window Name"
                variant="outlined"
                onBlur={(e) => {
                  setStoreValue("captureWindow", e.currentTarget.value);
                }}
                onChange={(e) => setCurWindowName(e.currentTarget.value)} // This is just used for disabling the preview buttons when empty.
                defaultValue={captureWindow}
                fullWidth
                multiline
                size="small"
              />
            ),
            "Preview Window": (
              <Button
                sx={{ mt: 8 }}
                variant="contained"
                color="secondary"
                fullWidth
                onClick={handlePreviewCaptureWindow}
                disabled={curWindowName.length == 0}
              >
                Preview Window
              </Button>
            ),
            "Preview Window With First Box": (
              <Stack spacing={2}>
                <Typography align="center" variant="h6">
                  Preview Window With Box
                </Typography>
                {boxes.map((b: any) => (
                  <Button
                    variant="outlined"
                    color="secondary"
                    fullWidth
                    onClick={() => handlePreviewCaptureWindowWithBox(b)}
                    key={b.boxId}
                    disabled={curWindowName.length == 0}
                  >
                    Preview - {getBoxDisplayName(b)}
                  </Button>
                ))}
              </Stack>
            ),
          },
          Debugging: {
            /* Doesn't work with Gem. "Trigger Force Stop": (
              <>
                <Button
                  sx={{ mt: 8 }}
                  variant="contained"
                  color="warning"
                  fullWidth
                  onClick={handleCircuitBreak}
                >
                  Trigger Force Stop
                </Button>
                <Typography variant="caption" color="info">
                  Immediately stops any active translation job.
                </Typography>
              </>
            ),*/
            /* Seed fixing currently disabled since we're using Gem as the mainline model. "Fix Seed": (
              <>
                <Button
                  sx={{ mt: 8 }}
                  variant="outlined"
                  color="primary"
                  fullWidth
                  onClick={handleFixSeed}
                >
                  Fix Seed
                </Button>
                <Typography variant="caption" color="info">
                  Resets the model seed to allow for deterministic results, even
                  if using a random translation algorithm such as MBR Sampling.
                  No effect otherwise.
                </Typography>
              </>
            ),*/
            "Open Logs": (
              <Button
                sx={{ mt: 8 }}
                variant="outlined"
                color="info"
                fullWidth
                onClick={handleOpenLogsFolder}
              >
                Open Logs Folder
              </Button>
            ),
            "Reset Settings": (
              <>
                <Button
                  sx={{ mt: 32 }}
                  variant="outlined"
                  color="info"
                  fullWidth
                  onDoubleClick={handleResetSettings}
                >
                  Reset Settings
                </Button>
                <Typography variant="caption" color="info">
                  Resets ALL settings - including those related to the detached
                  text boxes. Double click to activate.
                </Typography>
              </>
            ),
          },
        }}
      />
    </BaseView>
  );
};

export default GlobalOptionsView;
