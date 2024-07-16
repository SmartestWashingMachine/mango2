import React from "react";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { expect, it, jest } from "@jest/globals";
import ImageEditor from "./ImageEditor";
import { createStubAnnotation } from "../../../../../__stubs__/Annotation.stub";

jest.mock("react-colorful", () => ({
  HexColorPicker: () => <div></div>,
}));

jest.mock("uuid", () => ({
  v4: () => "abc",
}));

jest.mock("../../utils/mainGateway", () => ({
  MainGateway: {
    getStoreData: () => {},
    setStoreData: () => {},
  },
}));

(window as any).ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

it("should allow text to rotate", async () => {
  act(() => {
    render(
      <ImageEditor
        src=""
        annotations={[createStubAnnotation()]}
        originalImageHeight={1}
        originalImageWidth={1}
        fontFamilies={[]}
        onSaveImage={() => {}}
      />
    );
  });
  const elem = await screen.findByTestId("image-preview-box");
  const handle = elem.querySelector(".react-draggable-handle") as HTMLElement;
  const annotationText = await screen.findByTestId("annotation-text");
  const initialTransform = annotationText.style.transform;

  fireEvent.mouseDown(handle, { clientX: 0, clientY: 0 });
  fireEvent.mouseMove(handle, { clientX: 100, clientY: 100 });
  fireEvent.mouseUp(handle);

  expect(annotationText.style.transform).not.toBe(initialTransform);
});
