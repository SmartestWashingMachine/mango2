import React from "react";
import { faker } from "@faker-js/faker";
import { render, screen } from "@testing-library/react";
import { expect, it } from "@jest/globals";
import ImageEditorItem from "./ImageEditorItem";
import { createStubAnnotation } from "../../../../../__stubs__/Annotation.stub";

it("positions annotations correctly (1)", async () => {
  const containerWidth = faker.number.int({ min: 100, max: 4000 });
  const containerHeight = faker.number.int({ min: 100, max: 4000 });
  const imageWidth = faker.number.int({ min: 100, max: 4000 });
  const imageHeight = faker.number.int({ min: 100, max: 4000 });
  const x1 = imageWidth;
  const y1 = imageHeight;
  render(
    <ImageEditorItem
      originalImageWidth={imageWidth}
      originalImageHeight={imageHeight}
      containerWidth={containerWidth}
      containerHeight={containerHeight}
      onSelect={() => {}}
      canDrag
      a={{ ...createStubAnnotation(), x1, y1 }}
    />
  );

  const elem = screen.getByTestId("custom-annotation");
  expect(elem.style.left).toEqual("100%");
  expect(elem.style.top).toEqual("100%");
});

it("positions annotations correctly (2)", async () => {
  const containerWidth = faker.number.int({ min: 100, max: 4000 });
  const containerHeight = faker.number.int({ min: 100, max: 4000 });
  const imageWidth = faker.number.int({ min: 100, max: 4000 });
  const imageHeight = faker.number.int({ min: 100, max: 4000 });
  const x1 = 0;
  const y1 = 0;
  render(
    <ImageEditorItem
      originalImageWidth={imageWidth}
      originalImageHeight={imageHeight}
      containerWidth={containerWidth}
      containerHeight={containerHeight}
      onSelect={() => {}}
      canDrag
      a={{ ...createStubAnnotation(), x1, y1 }}
    />
  );

  const elem = screen.getByTestId("custom-annotation");
  expect(elem.style.left).toEqual("0%");
  expect(elem.style.top).toEqual("0%");
});
