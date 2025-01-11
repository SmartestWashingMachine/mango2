import { Tooltip } from "@mui/material";
import React, { useEffect, useState, useCallback } from "react";

type Annotation = {
  text: string;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
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

  return (
    <div className={fitImage ? "imagePreviewBoxOuter" : undefined}>
      <div className={fitImage ? "imagePreviewBox" : undefined}>
        <img src={src} className={className} onClick={onClick} />
        {annotations.map((a, idx) => (
          <Tooltip
            title={
              <h4 style={{ fontSize: "1.5em", fontWeight: "normal" }}>
                {a.text}
              </h4>
            }
            key={`${a.x1}-${a.y1}-${a.x2}-${a.y2}`}
            enterDelay={0}
            arrow
          >
            <div
              style={{
                //// width: (a.x2 - a.x1), height: (a.y2 - a.y1),
                //transform: `translate(${a.x1}px, ${a.y1}px)`,
                width: `${calcWidth(a)}%`,
                height: `${calcHeight(a)}%`,
                left: `${calcLeft(a)}%`,
                top: `${calcTop(a)}%`,
              }}
              className="annotation"
              data-testid={`annotation-${idx}`}
            ></div>
          </Tooltip>
        ))}
      </div>
    </div>
  );
};

export default AnnotatedImage;
