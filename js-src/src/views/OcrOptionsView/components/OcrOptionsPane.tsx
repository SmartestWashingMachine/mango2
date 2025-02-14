import React from "react";
import { MenuItem, Stack, TextField, Tooltip, Typography } from "@mui/material";
import { HexColorPicker } from "react-colorful";
import KeySelect from "../../../components/KeySelect";
import { BoxOptions } from "../../../types/BoxOptions";
import { OPTIONS_PRESETS } from "../../../utils/boxPresets";
import UpdateCheckbox from "../../../components/UpdateCheckbox";
import PaginatedTabs from "../../../components/PaginatedTabs";

export type OcrOptionsPaneProps = BoxOptions & {
  boxId: string;
  setStoreValue: (boxId: string, key: string, value: any) => void;
  goTextTab: () => void;
  boxButtons: any;
  createBox: any;
  removeBox: any;
};

const OcrOptionsPane = (props: OcrOptionsPaneProps) => {
  const changeValue = (key: string, value: any) => {
    props.setStoreValue(props.boxId, key, value);
  };

  const updateFontSize = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { value } = e.currentTarget;
    const parsed = parseInt(value, 10);

    if (!Number.isSafeInteger(parsed) || parsed < 1) return;

    changeValue("fontSize", parsed);
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
    const parsed = parseInt(value, 10);

    if (!Number.isSafeInteger(parsed) || parsed < 0) return;

    changeValue("autoEnterTime", parsed);
  };

  const updateActivationKey = (key: string) =>
    changeValue("activationKey", key);

  const updateHideKey = (key: string) => changeValue("hideKey", key);

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

    props.goTextTab();
  };

  return (
    <PaginatedTabs
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
                <MenuItem value={b.presetName} key={b.presetName}>
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
              tooltip="Disabled boxes will not show on the screen or do anything."
              helperText="The box can be enabled or disabled for the time being if unchecked."
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
          "Text Position": (
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
              tooltip="Boldens some of the text. Supposedly helps readability."
              helperText="Text will always be aligned to left if enabled."
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
            <Tooltip
              title="If greater than 0, then after being translated, the box will fade out in that many seconds. Hovering the mouse over the box shows it again."
              placement="top-start"
            >
              <TextField
                label="Fade Away Time"
                variant="standard"
                onChange={updateFadeAwayTime}
                defaultValue={props.fadeAwayTime}
              />
            </Tooltip>
          ),
        },
        Actions: {
          "Activation Key": props.activationKey ? (
            <KeySelect
              label="Activation Key"
              onKeyChange={updateActivationKey}
              value={props.activationKey}
              tooltip="Which key to press to translate the box contents. Press ESCAPE to disable."
            />
          ) : (
            <div></div>
          ),
          "Pause Key": props.pauseKey ? (
            <KeySelect
              label="Pause Key"
              onKeyChange={updatePauseKey}
              value={props.pauseKey}
              tooltip="While paused, neither auto scan nor clipboard copying will be auto translated. Only the activation key will work. Press ESCAPE to disable."
            />
          ) : (
            <div></div>
          ),
          "Hide Key": props.hideKey ? (
            <KeySelect
              label="Hide Key"
              onKeyChange={updateHideKey}
              value={props.hideKey}
              tooltip="While hidden, the box will not show on the screen. Press ESCAPE to disable."
            />
          ) : (
            <div></div>
          ),
          "Editing Key": props.spellingCorrectionKey ? (
            <KeySelect
              label="Spelling Correction Key"
              onKeyChange={updateSpellingCorrectionKey}
              value={props.spellingCorrectionKey}
              tooltip="Refines the translation with the spelling correction model. Must listen to clipboard. Press ESCAPE to disable."
            />
          ) : (
            <div></div>
          ),
          "Auto Scan Background": (
            <UpdateCheckbox
              changeValue={changeValue}
              defaultValue={props.autoScan}
              keyName="autoScan"
              tooltip="Every few seconds, automatically translate the box contents if the contents have changed significantly."
              label="Auto Scan Background"
            />
          ),
          "Listen to Clipboard": (
            <UpdateCheckbox
              changeValue={changeValue}
              defaultValue={props.listenClipboard}
              keyName="listenClipboard"
              tooltip="Automatically translate the box contents whenever the clipboard has changed, using the clipboard as the contents."
              label="Listen to Clipboard"
            />
          ),
          "Auto Enter": (
            <Tooltip
              title="If greater than 0, then after being translated, the ENTER key will be automatically pressed after that many seconds."
              placement="top-start"
            >
              <TextField
                label="Auto Enter"
                variant="standard"
                onChange={updateAutoEnterTime}
                defaultValue={props.autoEnterTime}
              />
            </Tooltip>
          ),
        },
        Performance: {
          "Stream Output": (
            <UpdateCheckbox
              changeValue={changeValue}
              defaultValue={props.useStream}
              keyName="useStream"
              tooltip="The box will show each token as it's being generated from the model."
              label="Stream Output"
            />
          ),
          "Enhance Text Recognition": (
            <UpdateCheckbox
              changeValue={changeValue}
              defaultValue={props.textDetect}
              keyName="textDetect"
              tooltip="Uses the text detection model before the text recognition model to enhance accuracy at the cost of speed. No effect on boxes that listen to the clipboard."
              label="Enhance Text Recognition"
            />
          ),
          "Is Speaker Box": (
            <UpdateCheckbox
              changeValue={changeValue}
              defaultValue={props.speakerBox}
              keyName="speakerBox"
              tooltip="If enabled, may improve the translation output of the other boxes. Place this box over the area where the speaker is usually given."
              label="Is Speaker Box"
            />
          ),
          "Remove Speaker": (
            <UpdateCheckbox
              changeValue={changeValue}
              defaultValue={props.removeSpeaker}
              keyName="removeSpeaker"
              tooltip="Removes the speaker name from the translated text given by the speaker box."
              label="Remove Speaker"
            />
          ),
        },
      }}
    />
  );
};

export default OcrOptionsPane;
