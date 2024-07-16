import React from "react";
import { render, screen } from "@testing-library/react";
import { expect, it } from "@jest/globals";
import AnnotatedImage from "./AnnotatedImage";
import { createStubAnnotation } from "../../../../../__stubs__/Annotation.stub";

type PositionAndSizeTestOptions = {
  originalImageWidth: number;
  originalImageHeight: number;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  expectedLeft: string;
  expectedTop: string;
  expectedWidth: string;
  expectedHeight: string;
};

const positionAndSizeTest = async (opts: PositionAndSizeTestOptions) => {
  const {
    originalImageWidth,
    originalImageHeight,
    expectedLeft,
    expectedTop,
    expectedWidth,
    expectedHeight,
    x1,
    y1,
    x2,
    y2,
  } = opts;

  const annotation = createStubAnnotation({ x1, y1, x2, y2 });
  render(
    <AnnotatedImage
      src=""
      originalImageWidth={originalImageWidth}
      originalImageHeight={originalImageHeight}
      annotations={[annotation]}
    />
  );

  const elem = await screen.findByTestId("annotation-0");
  expect(elem).toBeTruthy();
  expect(elem.style.left).toBe(expectedLeft);
  expect(elem.style.top).toBe(expectedTop);
  expect(elem.style.width).toBe(expectedWidth);
  expect(elem.style.height).toBe(expectedHeight);
};

it("sizes and positions an annotation right (1)", async () => {
  return positionAndSizeTest({
    originalImageWidth: 1000,
    originalImageHeight: 1000,
    x1: 0,
    y1: 0,
    x2: 250,
    y2: 425,
    expectedLeft: "0%",
    expectedTop: "0%",
    expectedWidth: "25%",
    expectedHeight: "42.5%",
  });
});

it("sizes and positions an annotation right (2)", async () => {
  return positionAndSizeTest({
    originalImageWidth: 300,
    originalImageHeight: 300,
    x1: 150,
    y1: 150,
    x2: 300,
    y2: 300,
    expectedLeft: "50%",
    expectedTop: "50%",
    expectedWidth: "50%",
    expectedHeight: "50%",
  });
});
