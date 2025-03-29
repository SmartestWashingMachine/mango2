import React, { useEffect, useState } from "react";
import { BoxOptionsFrontend } from "../../../types/BoxOptions";
import OcrBoxPane from "../../OcrBoxView/components/BoxPane";
import { Checkbox, FormControlLabel, Stack } from "@mui/material";

const DUMMY_TEXT = "Are you thinking outside of the box?";

export type BoxPanePreviewProps = {
  boxId: string;
};

const BoxPanePreview = ({ boxId }: BoxPanePreviewProps) => {
  const [options, setOptions] = useState<BoxOptionsFrontend | null>(null);

  const [simulatedLoading, setSimulatedLoading] = useState(false);
  const [simulatedDark, setSimulatedDark] = useState(false);

  /**
   * Retrieve initial box data from the electron backend.
   */
  useEffect(() => {
    const w = window as any;
    let didCancel = false;

    const asyncCb = async () => {
      const data = await w.electronAPI.getStoreData();

      if (didCancel || !data) return;

      const boxOptions = data.boxes.find((o: any) => o.boxId === boxId);
      if (boxOptions) {
        setOptions(boxOptions);
      }
    };

    asyncCb();

    return () => {
      didCancel = true;
    };
  }, [boxId]);

  if (!options) return null;

  return (
    <Stack spacing={4}>
      <div
        className={
          simulatedDark
            ? "boxPanePreviewContainerDark"
            : "boxPanePreviewContainerLight"
        }
      >
        <div className="boxPanePreviewInner">
          <OcrBoxPane
            loading={simulatedLoading}
            text={DUMMY_TEXT}
            prevTexts={
              options?.append
                ? ["Previous text 1", "Previous text 2", "Previous text 3"]
                : []
            }
            {...options}
            loadingOpacity={options?.useStream ? 0.75 : 0.25}
            pause={false}
            hide={false}
            boxId={boxId}
          />
        </div>
      </div>
      <Stack spacing={2}>
        <FormControlLabel
          control={
            <Checkbox
              onChange={(e) => {
                setSimulatedLoading(e.currentTarget.checked);
              }}
              checked={simulatedLoading}
              color="info"
            />
          }
          label="Is Loading"
        />
        <FormControlLabel
          control={
            <Checkbox
              onChange={(e) => {
                setSimulatedDark(e.currentTarget.checked);
              }}
              checked={simulatedDark}
              color="info"
            />
          }
          label="Use Dark Background"
        />
      </Stack>
    </Stack>
  );
};

export default BoxPanePreview;
