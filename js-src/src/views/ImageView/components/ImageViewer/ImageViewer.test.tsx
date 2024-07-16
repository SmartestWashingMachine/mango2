import React from "react";
import { faker } from "@faker-js/faker";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { expect, it, jest } from "@jest/globals";
import ImageViewer, { ImageViewerProps } from "./ImageViewer";

jest.mock("react-colorful", () => ({
  HexColorPicker: () => <div></div>,
}));

jest.mock("uuid", () => ({
  v4: () => "abc",
}));

jest.mock("../../../../utils/mainGateway", () => ({
  MainGateway: {
    openAMG: (s: string) => ({
      image: s,
      annotations: [],
    }),
    getStoreData: () => {},
    setStoreData: () => {},
  },
}));

(window as any).ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

Object.defineProperty(document, "fonts", {
  value: [],
});

const createImageViewer = (opts?: Partial<ImageViewerProps>) => {
  return (
    <ImageViewer
      imagePaths={[]}
      selectedPath={null}
      onFilesSelected={jest.fn()}
      selectDisabled={false}
      loadingProgress={0}
      pendingImageNames={[]}
      onSaveEditedImage={jest.fn()}
      {...opts}
    />
  );
};

it("should show an empty field when there are no files to show", async () => {
  await act(async () => {
    render(createImageViewer());
  });

  expect(screen.getByTestId("empty-viewer")).toBeTruthy();
});

it("should only show the selected file name in the preview even when given a full path", async () => {
  const imagePaths = ["abc/d.png", "abc/e.amg"];
  await act(async () => {
    render(createImageViewer({ imagePaths, selectedPath: imagePaths[0] }));
  });

  expect(screen.queryByTestId("empty-viewer")).not.toBeTruthy();
  expect(screen.queryByText("abc/d")).not.toBeTruthy();
  expect(screen.getByText("d.png")).toBeTruthy();
});

it("should show an edit button when the selected file is an AMG", async () => {
  const imagePaths = ["abc/1d.amg", "abc/ea.png"];
  await act(async () => {
    render(createImageViewer({ imagePaths, selectedPath: imagePaths[0] }));
  });

  expect(screen.getByText(/Edit/)).toBeTruthy();
});

it("should not show an edit button when the selected file is a PNG", async () => {
  const imagePaths = ["abc/1d.png", "abc/ea.amg"];
  await act(async () => {
    render(createImageViewer({ imagePaths, selectedPath: imagePaths[0] }));
  });

  expect(screen.queryByText(/Edit/)).not.toBeTruthy();
});

it("should show the ImageEditor when the edit button is clicked", async () => {
  const imagePaths = ["abc/1d.amg", "abc/ea.png"];
  await act(async () => {
    render(createImageViewer({ imagePaths, selectedPath: imagePaths[0] }));
  });
  const editButton = screen.getByText(/Edit/);

  await act(async () => {
    fireEvent.click(editButton);
  });

  expect(screen.getByTestId("image-preview-box")).toBeTruthy();
});

it("should show the first image and the last page button to navigate to the final image", async () => {
  const imagePaths = ["abc/1d.amg", "abc/ea.png", "abc/ce.png", "abc/deaa.png"];
  await act(async () => {
    render(createImageViewer({ imagePaths, selectedPath: imagePaths[0] }));
  });

  expect(screen.getByText(1)).toBeTruthy();
  expect(screen.queryByText("deaa.png")).not.toBeTruthy();
  const finalButton = screen.getByText(imagePaths.length);
  expect(finalButton).toBeTruthy();
  await act(async () => {
    fireEvent.click(finalButton);
  });

  expect(screen.getByText("deaa.png")).toBeTruthy();
});
