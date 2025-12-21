import { Tooltip, Typography } from "@mui/material";
import React, { useEffect, useState, useCallback } from "react";
import { useImageViewMode } from "../../../../components/ImageViewModeProvider";
import { getColorForIndex } from "./getColorForIndex";

type Annotation = {
  text: string;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  uuid: string;
};

type AnnotatedImageProps = {
  src: string;
  annotations: Annotation[];
  className?: string;
  originalImageWidth: number;
  originalImageHeight: number;
  fitImage: boolean;
  onClick?: () => void;
};

const AnnotatedImage = ({
  src,
  annotations,
  className,
  originalImageWidth,
  originalImageHeight,
  fitImage,
  onClick,
}: AnnotatedImageProps) => {
  const {
    viewingAnnotationIdx,
    setViewingAnnotationIdx,
    viewingAnnotationTextIdx,
  } = useImageViewMode();

  const [loaded, setLoaded] = useState(false); // Image loading.

  const calcWidth = (a: Annotation) => {
    const width = a.x2 - a.x1;

    return (width / (originalImageWidth || 1)) * 100;
  };

  const calcHeight = (a: Annotation) => {
    const height = a.y2 - a.y1;

    return (height / (originalImageHeight || 1)) * 100;
  };

  const calcLeft = (a: Annotation) => {
    return (a.x1 / (originalImageWidth || 1)) * 100;
  };

  const calcTop = (a: Annotation) => {
    return (a.y1 / (originalImageHeight || 1)) * 100;
  };

  const onLoad = () => {
    setLoaded(true);
  };

  // I'm not sure what the default <img> display prop is. TODO
  const imgStyles: any = {};
  if (!loaded) imgStyles["display"] = "none";

  return (
    <div className={fitImage ? "imagePreviewBoxOuter" : undefined}>
      <div className={fitImage ? "imagePreviewBox" : undefined}>
        <img
          src={src}
          className={className}
          onClick={onClick}
          onLoad={onLoad}
          style={imgStyles}
        />
        {annotations.map((a, idx) => (
          <div
            key={`${a.x1}-${a.y1}-${a.x2}-${a.y2}`}
            style={{
              //// width: (a.x2 - a.x1), height: (a.y2 - a.y1),
              //transform: `translate(${a.x1}px, ${a.y1}px)`,
              width: `${calcWidth(a)}%`,
              height: `${calcHeight(a)}%`,
              left: `${calcLeft(a)}%`,
              top: `${calcTop(a)}%`,
              color: getColorForIndex(idx),
              borderColor: getColorForIndex(idx),
              border:
                viewingAnnotationIdx === idx || viewingAnnotationTextIdx === idx
                  ? "2.5px solid"
                  : "1.5px solid",
            }}
            className="annotation"
            data-testid={`annotation-${idx}`}
            onMouseEnter={() => {
              setViewingAnnotationIdx(idx);
            }}
            onMouseLeave={() => {
              setViewingAnnotationIdx(0);
            }}
          >
            <span className="annotation-label">{idx + 1}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AnnotatedImage;
