import { Button, MenuItem, Stack, Typography } from "@mui/material";
import React, { useState, useEffect } from "react";
import ReplaceTermsList from "./components/ReplaceTermsList";
import { setSeed } from "../../flaskcomms/optionsViewComms";
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

const GlobalOptionsView = () => {
  const pushAlert = useAlerts();

  const [terms, setTerms] = useState<IReplaceTerm[]>([]);

  const [isLoading, setIsLoading] = useState(true);

  const [installedModels, setInstalledModels] = useState<string[]>([]);

  const [loadedData, setLoadedData] = useState<any>({});

  useEffect(() => {
    let didCancel = false;

    const asyncCb = async () => {
      const data = await MainGateway.getStoreData();

      if (!didCancel) {
        setLoadedData(data);
        setTerms(data.terms);

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
    };
    const removeCb = MainGateway.listenStoreDataChange(cb);

    return () => {
      removeCb();
    };
  }, []);

  useEffect(() => {
    // Retrieve allowed models from the backend API.
    let canceled = false;

    const cb = async () => {
      if (canceled) return;

      const installedMap = await getInstalledModels();
      // Return model names only if they are truthy (installed).
      setInstalledModels(
        Object.entries(installedMap)
          .filter((x) => x[1])
          .map((x) => x[0])
      );
    };

    cb();

    return () => {
      canceled = true;
    };
  }, []);

  const setStoreValue = async (key: string, value: any) => {
    await MainGateway.setStoreValue(key, value);

    await MainGateway.resendData();

    setLoadedData((d: any) => ({ ...d, [key]: value, }));
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

  const handleFixSeed = async () => {
    await setSeed(42);
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

  const handleResetSettings = async () => {
    await MainGateway.resetSettings();

    const data = await MainGateway.getStoreData();
    setLoadedData(data);

    pushAlert('Settings reset!');
  };

  const itemEnabled = (x: { name: string; value: string; desc: string }) => {
    const allowedItems = ["None", "MAP Beam Decoding", "MBR Sampling", "MBR Beam Sampling"];
    if (allowedItems.includes(x.name)) return true;
    return installedModels.indexOf(x.value) !== -1;
  };

  const renderItem = (x: { name: string; value: string; desc: string }) => [
    <MenuItem
      value={x.value}
      dense
      disabled={!itemEnabled(x)}
    >
      {x.name}
    </MenuItem>,
    <MenuItem disabled value="" divider dense>
      <em style={{ fontSize: "small" }}>{x.desc}</em>
    </MenuItem>,
  ];

  if (isLoading) return <div></div>;

  const { textLineModelName, textDetectionModelName, textRecognitionModelName, translationModelName, rerankingModelName, spellCorrectionModelName, enableCuda, forceTranslationCPU, forceTdCpu, contextAmount, autoOpenOcrWindow, decodingMode, numBeams, topK, topP, epsilonCutoff, lengthPenalty, noRepeatNgramSize, temperature, repetitionPenalty, maxLengthA } = loadedData;

  const decodingParamsIgnored = decodingMode === 'beam';

  return (
    <BaseView>
      <PaginatedTabs
        items={{
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
                helperText="May improve speed IF using a good GPU that supports CUDA."
              />
            ),
            "Force TDs on CPU": (
              <UpdateCheckbox
                changeValue={setStoreValue}
                keyName="forceTdCpu"
                defaultValue={forceTdCpu}
                tooltip="Has no effect if CUDA is disabled."
                label="Force TDs on CPU"
                helperText="The text and text line detection models will ALWAYS be on the CPU rather than the GPU. Can decrease memory usage at the cost of speed."
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
            "Auto Open OCR Window": (
              <UpdateCheckbox
                changeValue={setStoreValue}
                keyName="autoOpenOcrWindow"
                defaultValue={autoOpenOcrWindow}
                tooltip="Automatically open the OCR window when the Text tab is selected."
                label="Auto Open OCR Window"
              />
            ),
          },
          "Translation Algorithm": {
            "Only change these settings if": (
              <Typography align="center" variant="body2">
                Only change these settings if you know what you're doing. Most
                settings only take effect with MBR Beam Sampling or MBR Greedy
                Decoding.
              </Typography>
            ),
            "Decoding Mode": (
              <UpdateListField
                changeValue={setStoreValue}
                keyName="decodingMode"
                defaultValue={decodingMode}
                label="Decoding Mode"
                helperText="May improve translation quality. Most reranking methods only work on Japanese-2-English models."
              >
                {DECODING_OPTIONS.map(renderItem)}
              </UpdateListField>
            ),
            Beams: (
              <UpdateNumberField
                label="Beams"
                changeValue={setStoreValue}
                keyName="numBeams"
                defaultValue={numBeams}
                helperText="Max number of beams or candidates to use from the translation model. Increasing this will lower speed but may improve the translation quality."
                valueType="int"
                safeValue={2}
                minValue={1}
                maxValue={50}
              />
            ),
            "Top K": (
              <UpdateNumberField
                label="Top K"
                changeValue={setStoreValue}
                keyName="topK"
                defaultValue={topK}
                helperText="Every decoding step, only allow the top K predicted tokens to be sampled. A good starter value may be 50."
                valueType="int"
                safeValue={0}
                minValue={0}
                disabled={decodingParamsIgnored}
              />
            ),
            "Top P": (
              <UpdateNumberField
                label="Top P"
                changeValue={setStoreValue}
                keyName="topP"
                defaultValue={topP}
                helperText="Every decoding step, only the smallest set of tokens with probs adding up to P or higher can be sampled. Set this between [0, 1)."
                valueType="float"
                safeValue={0}
                disabled={decodingParamsIgnored}
              />
            ),
            "Epsilon Cutoff": (
              <UpdateNumberField
                label="Epsilon Cutoff"
                changeValue={setStoreValue}
                keyName="epsilonCutoff"
                defaultValue={epsilonCutoff}
                helperText="Every decoding step, tokens with a probability lower than this are cut off. Set this between [0, 1). A good starter value may be 0.03."
                valueType="float"
                safeValue={0.0}
                disabled={decodingParamsIgnored}
              />
            ),
            Temperature: (
              <UpdateNumberField
                label="Temperature"
                changeValue={setStoreValue}
                keyName="temperature"
                defaultValue={temperature}
                helperText="Setting this greater than 0 may increase translation diversity, and vice versa as it goes towards 0."
                valueType="float"
                safeValue={1.0}
                disabled={decodingParamsIgnored}
              />
            ),
            "Length Penalty": (
              <UpdateNumberField
                label="Length Penalty"
                changeValue={setStoreValue}
                keyName="lengthPenalty"
                defaultValue={lengthPenalty}
                helperText="Setting this greater than 0 encourages longer translations."
                valueType="float"
                safeValue={1.0}
              />
            ),
            "No Repeat N-Gram Size": (
              <UpdateNumberField
                label="No Repeat N-Gram Size"
                changeValue={setStoreValue}
                keyName="noRepeatNgramSize"
                defaultValue={noRepeatNgramSize}
                helperText="N-grams of the given size will not be repeated in the translations."
                valueType="int"
                safeValue={5}
                minValue={1}
                maxValue={99}
              />
            ),
            "Repetition Penalty": (
              <UpdateNumberField
                label="Repetition Penalty"
                changeValue={setStoreValue}
                keyName="repetitionPenalty"
                defaultValue={repetitionPenalty}
                helperText="Setting this greater than 1.0 discourages repeated words."
                valueType="float"
                safeValue={1.2}
              />
            ),
            "Max Length A": (
              <UpdateNumberField
                label="Max Length A"
                keyName="maxLengthA"
                changeValue={setStoreValue}
                defaultValue={maxLengthA}
                placeholder="Set to 0 to disable the A length limit."
                helperText="The output sentence can be up to A times as long as the input sentence."
                valueType="float"
                safeValue={0}
                minValue={0}
                maxValue={500}
              />
            ),
          },
          Terms: {
            Terms: (
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
          "Import Files": {
            "Open Models Folder": (
              <>
                <Button
                  sx={{ mt: 8 }}
                  variant="contained"
                  color="primary"
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
                  Font files can be placed in the folder for image editing purposes, or to change the font used by the OCR box.
                </Typography>
              </>
            ),
          },
          Debugging: {
            "Fix Seed": (
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
                <Button
                  sx={{ mt: 8 }}
                  variant="outlined"
                  color="info"
                  fullWidth
                  onClick={handleOpenLogsFolder}
                >
                  Open Logs Folder
                </Button>
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
                  Resets ALL settings - including those related to the OCR boxes. Double click to activate.
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
