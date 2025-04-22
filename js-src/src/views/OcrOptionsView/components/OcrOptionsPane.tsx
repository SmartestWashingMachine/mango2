import React from "react";
import { MenuItem, Stack, TextField, Typography } from "@mui/material";
import { HexColorPicker } from "react-colorful";
import { v4 as uuidv4 } from "uuid";
import KeySelect from "../../../components/KeySelect";
import { BoxOptions } from "../../../types/BoxOptions";
import { OPTIONS_PRESETS } from "../../../utils/boxPresets";
import UpdateCheckbox from "../../../components/UpdateCheckbox";
import PaginatedTabs from "../../../components/PaginatedTabs";
import { MainGateway } from "../../../utils/mainGateway";
import BoxPanePreview from "./BoxPanePreview";

export type OcrOptionsPaneProps = BoxOptions & {
  boxId: string;
  allBoxIds: string[];
  setStoreValue: (boxId: string, key: string, value: any) => void;
  goTextTab: () => void;
  boxButtons: any;
  createBox: any;
  removeBox: any;
};

const OcrOptionsPane = (props: OcrOptionsPaneProps) => {
  const [renderKey, setRenderKey] = React.useState<string>(uuidv4());

  const changeValue = (key: string, value: any) => {
    props.setStoreValue(props.boxId, key, value);
  };

  const updateFontSize = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { value } = e.currentTarget;
    const parsed = parseInt(value, 10);

    if (!Number.isSafeInteger(parsed) || parsed < 1) return;

    changeValue("fontSize", parsed);
  };

  const updateTranslateLinesIndividually = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const { value } = e.currentTarget;
    const parsed = parseInt(value, 10);

    if (!Number.isSafeInteger(parsed) || parsed < 0) return;

    changeValue("translateLinesIndividually", parsed);
  };

  const updateFontColor = (color: string) => changeValue("fontColor", color);

  const updateTextAlign = (e: React.ChangeEvent<HTMLInputElement>) =>
    changeValue("textAlign", e.target.value);

  const updateBackgroundColor = (color: string) =>
    changeValue("backgroundColor", color);

  const updateFadeAwayTime = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { value } = e.currentTarget;
    const parsed = parseInt(value, 10);

    if (!Number.isSafeInteger(parsed) || parsed < 0) return;

    changeValue("fadeAwayTime", parsed);
  };

  const updateAutoEnterTime = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { value } = e.currentTarget;
    const parsed = parseFloat(value);

    if (isNaN(parsed) || parsed < 0) return;

    changeValue("autoEnterTime", parsed);
  };

  const updatescanAfterEnter = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { value } = e.currentTarget;
    const parsed = parseFloat(value);

    if (isNaN(parsed) || parsed < 0) return;

    changeValue("scanAfterEnter", parsed);
  };

  const updatePipeOutput = (e: React.ChangeEvent<HTMLInputElement>) =>
    changeValue("pipeOutput", e.target.value);

  const updateActivationKey = (key: string) =>
    changeValue("activationKey", key);

  const updateHideKey = (key: string) => changeValue("hideKey", key);

  const updateClickThroughKey = (key: string) =>
    changeValue("clickThroughKey", key);

  const updateSpellingCorrectionKey = (key: string) =>
    changeValue("spellingCorrectionKey", key);

  const updateBackgroundOpacity = (e: React.ChangeEvent<HTMLInputElement>) =>
    changeValue("backgroundOpacity", e.currentTarget.value);

  const updateStrokeSize = (e: React.ChangeEvent<HTMLInputElement>) =>
    changeValue("strokeSize", e.currentTarget.value);

  const updateStrokeColor = (color: string) =>
    changeValue("strokeColor", color);

  const updatePauseKey = (key: string) => changeValue("pauseKey", key);

  const updatePreset = (e: any) => {
    const presetName = e.target.value;
    const preset = OPTIONS_PRESETS.find((x) => x.presetName === presetName);
    if (!preset) return;

    for (const [key, value] of Object.entries(preset.options)) {
      changeValue(key as any, value);
    }

    // Some presets modify the Box ID, making this util necessary.
    MainGateway.regenerateBoxManagers();

    // props.goTextTab();
    // Reset the render key to force a re-render of the tabs (as we use defaultValue instead of value for the fields).
    setRenderKey(uuidv4());
  };

  return (
    <PaginatedTabs
      boldFirst
      key={renderKey}
      headers={props.boxButtons}
      footers={
        <>
          {props.createBox}
          {props.removeBox}
        </>
      }
      showItems={!!props.boxId}
      itemsKey={props.boxId}
      items={{
        Preview: {
          Preview: <BoxPanePreview boxId={props.boxId} />,
        },
        Preset: {
          Presets: (
            <TextField
              onChange={updatePreset}
              defaultValue=""
              helperText="You can select a preset here for a quick configuration. Once selected, open the OCR box to see the changes."
              variant="standard"
              select
            >
              {OPTIONS_PRESETS.map((b) => [
                <MenuItem
                  value={b.presetName}
                  key={b.presetName}
                  disabled={b.disabled(props.allBoxIds)}
                >
                  {b.presetName}
                </MenuItem>,
                <MenuItem
                  disabled
                  value="disabledvalue"
                  divider
                  dense
                  key={b.description}
                >
                  <em style={{ fontSize: "small" }}>{b.description}</em>
                </MenuItem>,
              ])}
            </TextField>
          ),
          Enabled: (
            <UpdateCheckbox
              changeValue={changeValue}
              defaultValue={props.enabled}
              keyName="enabled"
              helperText="Disabled boxes will not show on the screen or do anything."
              label="Enabled"
            />
          ),
        },
        "Text Appearance": {
          "Text Size": (
            <TextField
              label="Text Size"
              variant="standard"
              type="number"
              onChange={updateFontSize}
              defaultValue={props.fontSize}
            />
          ),
          "Text Color": (
            <Stack spacing={2} sx={{ alignItems: "center" }}>
              <Typography variant="body1">Text Color</Typography>
              <HexColorPicker
                color={props.fontColor}
                onChange={updateFontColor}
              />
            </Stack>
          ),
          "Text Stroke Size": (
            <TextField
              label="Text Stroke Size"
              variant="standard"
              type="number"
              onChange={updateStrokeSize}
              defaultValue={props.strokeSize}
            />
          ),
          "Text Stroke Color": (
            <Stack spacing={2} sx={{ alignItems: "center" }}>
              <Typography variant="body1">Text Stroke Color</Typography>
              <HexColorPicker
                color={props.strokeColor}
                onChange={updateStrokeColor}
                defaultValue={props.strokeColor}
              />
            </Stack>
          ),
          "Text Align": (
            <TextField
              onChange={updateTextAlign}
              defaultValue={props.textAlign}
              label="Text Align"
              variant="standard"
              select
            >
              <MenuItem value="left">Left</MenuItem>
              <MenuItem value="center">Center</MenuItem>
              <MenuItem value="right">Right</MenuItem>
            </TextField>
          ),
          "Bionic Reading": (
            <UpdateCheckbox
              changeValue={changeValue}
              defaultValue={props.bionicReading}
              keyName="bionicReading"
              helperText="Boldens some of the text. Supposedly helps readability. Text will always be aligned to left if enabled."
              label="Bionic Reading"
            />
          ),
          "Mini Backlog": (
            <UpdateCheckbox
              changeValue={changeValue}
              defaultValue={props.append}
              keyName="append"
              helperText="Some of the past texts in the box will be displayed within it."
              label="Mini Backlog"
            />
          ),
        },
        "Box Appearance": {
          "Background Color": (
            <Stack spacing={2} sx={{ alignItems: "center" }}>
              <Typography variant="body1">Background Color</Typography>
              <HexColorPicker
                color={props.backgroundColor}
                onChange={updateBackgroundColor}
                defaultValue={props.backgroundColor}
              />
            </Stack>
          ),
          "Background Opacity": (
            <TextField
              label="Background Opacity"
              variant="standard"
              type="number"
              onChange={updateBackgroundOpacity}
              defaultValue={props.backgroundOpacity}
            />
          ),
          "Fade Away Time": (
            <TextField
              label="Fade Away Time"
              variant="standard"
              onChange={updateFadeAwayTime}
              defaultValue={props.fadeAwayTime}
              helperText="If greater than 0, then after being translated, the box will fade out in that many seconds. Hovering the mouse over the box shows it again."
            />
          ),
        },
        Actions: {
          "Activation Key": props.activationKey ? (
            <KeySelect
              label="Activation Key"
              onKeyChange={updateActivationKey}
              value={props.activationKey}
              helperText="Which key to press to translate the box contents. Press ESCAPE to disable."
            />
          ) : (
            <div></div>
          ),
          "Pause Key": props.pauseKey ? (
            <KeySelect
              label="Pause Key"
              onKeyChange={updatePauseKey}
              value={props.pauseKey}
              helperText="While paused, neither auto scan nor clipboard copying will be auto translated. Only the activation key will work. Press ESCAPE to disable."
            />
          ) : (
            <div></div>
          ),
          "Hide Key": props.hideKey ? (
            <KeySelect
              label="Hide Key"
              onKeyChange={updateHideKey}
              value={props.hideKey}
              helperText="While hidden, the box will not show on the screen. Press ESCAPE to disable."
            />
          ) : (
            <div></div>
          ),
          "Click Through Key":
            true || props.clickThroughKey ? (
              <KeySelect
                label="Click Through Key"
                onKeyChange={updateClickThroughKey}
                value={props.clickThroughKey}
                helperText="While enabled, you can click through the box. Helpful for Reader boxes."
              />
            ) : (
              <div></div>
            ),
          "Editing Key Spelling Correction Key": props.spellingCorrectionKey ? (
            <KeySelect
              label="Spelling Correction Key"
              onKeyChange={updateSpellingCorrectionKey}
              value={props.spellingCorrectionKey}
              helperText="Refines the translation with the spelling correction model. Must listen to clipboard. Press ESCAPE to disable."
            />
          ) : (
            <div></div>
          ),
          "Auto Scan Background": (
            <UpdateCheckbox
              changeValue={changeValue}
              defaultValue={props.autoScan}
              keyName="autoScan"
              helperText="Every few seconds, automatically translate the box contents if the contents have changed significantly."
              label="Auto Scan Background"
            />
          ),
          "Listen to Clipboard": (
            <UpdateCheckbox
              changeValue={changeValue}
              defaultValue={props.listenClipboard}
              keyName="listenClipboard"
              label="Listen to Clipboard"
              helperText="Automatically translate the box contents whenever the clipboard has changed, using the clipboard as the contents."
            />
          ),
          "Auto Enter": (
            <TextField
              label="Auto Enter"
              variant="standard"
              onChange={updateAutoEnterTime}
              defaultValue={props.autoEnterTime}
              helperText="If greater than 0, then after being translated, the ENTER key will be automatically pressed after that many seconds."
            />
          ),
          "Scan N Seconds After Enter": (
            <TextField
              label="Scan N Seconds After Enter"
              variant="standard"
              onChange={updatescanAfterEnter}
              defaultValue={props.scanAfterEnter}
              helperText="If greater than 0, then the background will be OCR'd after that many seconds whenever the ENTER key is pressed manually."
            />
          ),
          "Pipe Output": (
            <TextField
              onChange={updatePipeOutput}
              defaultValue={props.pipeOutput}
              variant="standard"
              select
              helperText="Pipe the output of this box to another box."
              label="Pipe Output"
            >
              <MenuItem value="Self">Self</MenuItem>
              {props.allBoxIds.map((b) => (
                <MenuItem value={b} key={b}>
                  {b}
                </MenuItem>
              ))}
            </TextField>
          ),
        },
        Performance: {
          "Stream Output": (
            <UpdateCheckbox
              changeValue={changeValue}
              defaultValue={props.useStream}
              keyName="useStream"
              helperText="The box will show each token as it's being generated from the model."
              label="Stream Output"
            />
          ),
          "Enhance Text Recognition": (
            <UpdateCheckbox
              changeValue={changeValue}
              defaultValue={props.textDetect}
              keyName="textDetect"
              helperText="Uses the text detection model before the text recognition model to enhance accuracy at the cost of speed. No effect on boxes that listen to the clipboard."
              label="Enhance Text Recognition"
            />
          ),
          "Is Speaker Box": (
            <UpdateCheckbox
              changeValue={changeValue}
              defaultValue={props.speakerBox}
              keyName="speakerBox"
              helperText="If enabled, may improve the translation output of the other boxes. Place this box over the area where the speaker is usually given."
              label="Is Speaker Box"
            />
          ),
          "Remove Speaker": (
            <UpdateCheckbox
              changeValue={changeValue}
              defaultValue={props.removeSpeaker}
              keyName="removeSpeaker"
              helperText="Removes the speaker name from the translated text given by the speaker box."
              label="Remove Speaker"
            />
          ),
          "Faster Activation Key Scanning": (
            <UpdateCheckbox
              changeValue={changeValue}
              defaultValue={props.fasterScan}
              keyName="fasterScan"
              helperText="Gives faster outputs using the Activation Key or 'Scan After Left Click' methods."
              label="Faster Activation Key Scanning"
            />
          ),
          "Enable Activation Key on Stubborn Apps": (
            <UpdateCheckbox
              changeValue={changeValue}
              defaultValue={props.serverSideActivationKey}
              keyName="serverSideActivationKey"
              helperText="Enable this AND 'Faster Activation Key Scanning' if an application is overriding the Activation Key or preventing it from working. But if this is enabled, the box MUST be manually hidden with the Hide Key before being activated."
              label="Enable Activation Key on Stubborn Apps"
            />
          ),
          "Activation Key Scanning Bottom N Lines Only": (
            <TextField
              label="Activation Key Scanning Bottom N Lines Only"
              variant="standard"
              type="number"
              onChange={updateTranslateLinesIndividually}
              defaultValue={props.translateLinesIndividually}
              helperText="If greater than 0, only that many of the bottom-most text lines will be scanned and translated, and each text line will be separately translated. This can be useful when attempting to translate system elements like a battle log."
            />
          ),
        },
      }}
    />
  );
};

export default OcrOptionsPane;
