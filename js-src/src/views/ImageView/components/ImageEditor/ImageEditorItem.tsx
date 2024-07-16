import React, { useEffect, useState } from "react";
import IAnnotation from "../../../../types/Annotation";
import Draggable, {
  DraggableEvent,
  DraggableData,
  ControlPosition,
} from "react-draggable";
import { Resizable } from "react-resizable";
import "react-resizable/css/styles.css";

export type ImageEditorProps = {
  a: IAnnotation;
  originalImageWidth: number;
  originalImageHeight: number;
  containerWidth: number;
  containerHeight: number;
  onSelect: () => void;
  canDrag: boolean;
};

const ImageEditorItem = ({
  a,
  originalImageWidth,
  originalImageHeight,
  containerWidth,
  containerHeight,
  onSelect,
  canDrag,
}: ImageEditorProps) => {
  const calcWidth = (a: IAnnotation) => {
    const width = a.x2 - a.x1;

    return width / (originalImageWidth || 1);
  };

  const calcHeight = (a: IAnnotation) => {
    const height = a.y2 - a.y1;

    return height / (originalImageHeight || 1);
  };

  const calcLeft = (a: IAnnotation) => {
    return (a.x1 / (originalImageWidth || 1)) * 100;
  };

  const calcTop = (a: IAnnotation) => {
    return (a.y1 / (originalImageHeight || 1)) * 100;
  };

  const [position, setPosition] = useState<ControlPosition>({ x: 0, y: 0 });
  const [boxWidth, setBoxWidth] = useState(calcWidth(a));
  const [boxHeight, setBoxHeight] = useState(calcHeight(a));

  const trueFontCalc = a.fontSize * 0.000957 * containerWidth;
  // Old formula: const trueStrokeCalc = ((a.strokeSize * 0.000957) / 8) * containerWidth;
  const trueStrokeCalc =
    ((a.strokeSize * a.fontSize * 0.000957) / 60) * containerWidth;

  const trueBoxWidth = boxWidth * containerWidth;
  const trueBoxHeight = boxHeight * containerHeight;

  const customStyles: React.CSSProperties = {
    fontSize: `${trueFontCalc}px`,
    // These webkit stroke effects SUCK!
    // WebkitTextStrokeWidth: `${trueStrokeCalc}px`,
    // WebkitTextStrokeColor: a.strokeColor,
    color: a.fontColor,
    borderRadius: `${a.borderRadius}px`,
    textAlign: a.textAlign as any,
    fontFamily: `"${a.fontFamily}"`,
  };

  if (a.strokeSize > 0)
    customStyles[
      "textShadow"
    ] = `-${trueStrokeCalc}px -${trueStrokeCalc}px 0 ${a.strokeColor}, ${trueStrokeCalc}px -${trueStrokeCalc}px 0 ${a.strokeColor}, -${trueStrokeCalc}px ${trueStrokeCalc}px 0 ${a.strokeColor}, ${trueStrokeCalc}px ${trueStrokeCalc}px 0 ${a.strokeColor}`;
  if (a.isBold) customStyles["fontWeight"] = "bold";
  if (a.isItalic) customStyles["fontStyle"] = "italic";
  if (a.hasBackgroundColor) customStyles["backgroundColor"] = a.backgroundColor;

  if (a.verticalCenter) {
    customStyles["flexDirection"] = "column";
    customStyles["justifyContent"] = "center";
    customStyles["display"] = "flex";
  }

  const onStart = (event: DraggableEvent, data: DraggableData) => {
    const { node } = data;

    setPosition({
      x: (parseFloat(node.style.left) * containerWidth) / 100,
      y: (parseFloat(node.style.top) * containerHeight) / 100,
    });

    node.style.left = "0";
    node.style.top = "0";
  };

  const onStop = (event: DraggableEvent, data: DraggableData) => {
    const { x, y, node } = data;

    const newX = (x / containerWidth) * 100;
    const newY = (y / containerHeight) * 100;

    node.style.left = newX + "%";
    node.style.top = newY + "%";

    setPosition({
      x: 0,
      y: 0,
    });
  };

  const onkeydownInEditable = (e: React.KeyboardEvent<HTMLDivElement>) => {
    const selection = window.getSelection();
    // Don't allow deleting nodes
    if (!selection || !selection.focusNode || !selection.anchorNode) return;

    if (selection.focusNode.nodeName === "SPAN") e.preventDefault();
  };

  const [rotation, setRotation] = useState(0);

  const handleRotate = (e: DraggableEvent, data: DraggableData) => {
    setRotation(rotation + data.deltaX);
  };

  // Since text here is not propagated to ImageEditor, setting a global preset could reset text which we do NOT want.
  // To rectify this, we only read the text from above once.
  const [initialText, setInitialText] = useState<string | null>(null);
  useEffect(() => {
    if (initialText === null) setInitialText(a.text);
  }, [a, initialText]);

  if (initialText === null) return null;

  return (
    <Draggable
      position={position}
      onDrag={handleRotate}
      cancel={".react-resizable-handle"}
      handle=".react-draggable-handle"
    >
      <Draggable
        onStart={onStart}
        onStop={onStop}
        position={position}
        cancel={".react-resizable-handle"}
        disabled={!canDrag}
      >
        <Resizable
          width={trueBoxWidth as any}
          height={trueBoxHeight as any}
          onResize={(e, data) => {
            setBoxWidth((data.size.width as any) / containerWidth);
            setBoxHeight((data.size.height as any) / containerHeight);
          }}
        >
          <div
            style={{
              ...customStyles,
              //width: `${calcWidth(a)}%`,
              //height: `${calcHeight(a)}%`,
              width: trueBoxWidth,
              height: trueBoxHeight,
              left: `${calcLeft(a)}%`,
              top: `${calcTop(a)}%`,
            }}
            onKeyDown={onkeydownInEditable}
            spellCheck="false"
            className="custom-annotation"
            onClick={onSelect}
            data-testid="custom-annotation"
          >
            <p
              contentEditable="true"
              suppressContentEditableWarning={true}
              style={{ transform: `rotate(${rotation}deg)` }}
              data-testid="annotation-text"
            >
              {initialText}
            </p>
            <span
              className="react-draggable-handle"
              contentEditable="false"
              suppressContentEditableWarning={true}
            ></span>
          </div>
        </Resizable>
      </Draggable>
    </Draggable>
  );
};

export default ImageEditorItem;
