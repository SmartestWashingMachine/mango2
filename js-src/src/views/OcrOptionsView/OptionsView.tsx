import { Button } from "@mui/material";
import React, { useState, useEffect } from "react";
import OcrOptionsPane from "./components/OcrOptionsPane";
import BaseView from "../BaseView";
import { MainGateway } from "../../utils/mainGateway";

export type OptionsViewProps = {
  goTextTab: () => void;
};

const OptionsView = (props: OptionsViewProps) => {
  const [boxesOptions, setBoxesOptions] = useState<any>([]);
  const [selId, setSelId] = useState("");

  useEffect(() => {
    let didCancel = false;

    const asyncCb = async () => {
      const data = await MainGateway.getStoreData();

      if (!didCancel) {
        setBoxesOptions(data.boxes);

        if (data.boxes.length > 0) {
          setSelId(data.boxes[0].boxId);
        }
      }
    };

    asyncCb();

    return () => {
      didCancel = true;
    };
  }, []);

  useEffect(() => {
    const cb = (e: any, s: any, oldS: any) => {
      if (s.boxes.length !== oldS.boxes.length || s.boxes.length === 0)
        setBoxesOptions(s.boxes);
    };
    const removeCb = MainGateway.listenStoreDataChange(cb);

    return () => {
      removeCb();
    };
  }, []);

  const setStoreValue = async (boxId: string, key: string, value: any) => {
    await MainGateway.setBoxValue(boxId, key, value);

    setBoxesOptions((d: any) => d.map((dBox: any) => boxId === dBox.boxId ? ({ ...dBox, [key]: value, }) : ({ ...dBox, })));
  };

  const removeBox = () => {
    const boxId = selId;
    if (!boxId) return;

    // We can't keep viewing a deleted box!
    const newBoxId = boxesOptions.find((x: any) => x.boxId !== boxId)?.boxId;
    setSelId(newBoxId || "");

    MainGateway.deleteOcrBox(boxId);
  };

  const createBox = () => {
    MainGateway.newOcrBox();
  };

  const handleTabChange = async (newValue: string) => {
    await getNewBoxData();
    setSelId(newValue);
  };

  const getNewBoxData = async () => {
    const data = await MainGateway.getStoreData();

    setBoxesOptions(data.boxes);
  };

  const selBoxOptions = (boxesOptions || []).find((x: any) => x.boxId === selId);

  return (
    <BaseView>
      <OcrOptionsPane
        {...selBoxOptions}
        setStoreValue={setStoreValue}
        goTextTab={props.goTextTab}
        createBox={
          <Button variant="text" onClick={createBox} color="info">
            New Box
          </Button>
        }
        removeBox={
          !!selId ? (
            <Button variant="text" onClick={removeBox} color="info">
              Delete Box ({selId.slice(0, 3)})
            </Button>
          ) : (
            <div></div>
          )
        }
        boxButtons={boxesOptions.map((x: any) => (
          <Button
            key={x.boxId}
            variant="text"
            onClick={() => handleTabChange(x.boxId)}
            sx={(theme) => ({
              fontWeight: x.boxId === selId ? "bold" : "normal",
              color: x.boxId === selId ? "white" : "hsl(291, 3%, 74%)",
            })}
          >
            {`Box (${x.boxId.slice(0, 3)})`}
          </Button>
        ))}
      />
    </BaseView>
  );
};

export default OptionsView;
