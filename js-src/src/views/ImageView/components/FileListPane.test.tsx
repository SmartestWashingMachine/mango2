import React from "react";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { beforeEach, describe, expect, it, jest } from "@jest/globals";
import FileListPane from "./FileListPane";
import FileInfo from "../../../types/FileInfo";

jest.mock("../../../utils/mainGateway", () => ({
  MainGateway: {
    showFile: () => {},
  },
}));

import { MainGateway } from "../../../utils/mainGateway";

it("still renders a library element if no rootItem is given", async () => {
  render(
    <FileListPane
      rootItem={null}
      selectedPath={null}
      onSelectFileInfo={jest.fn()}
      onRefresh={jest.fn()}
    />
  );

  expect(screen.getByText("Library")).toBeTruthy();
});

it("has a refresh and back button.", async () => {
  const rootItem: FileInfo = {
    fullPath: "",
    fileName: "",
    childrenItems: [],
  };
  render(
    <FileListPane
      rootItem={rootItem}
      selectedPath={null}
      onSelectFileInfo={jest.fn()}
      onRefresh={jest.fn()}
    />
  );

  expect(screen.getByTestId("back-button")).toBeTruthy();
  expect(screen.getByTestId("refresh-button")).toBeTruthy();
});

describe("Options menu", () => {
  let mockShowFile: () => void;

  beforeEach(() => {
    mockShowFile = jest.fn();

    MainGateway.showFile = mockShowFile;
  });

  it("does not open a context menu on root item", async () => {
    const rootItem: FileInfo = {
      fullPath: "items/base",
      fileName: "base",
      childrenItems: [],
    };

    render(
      <FileListPane
        rootItem={rootItem}
        selectedPath={null}
        onSelectFileInfo={jest.fn()}
        onRefresh={jest.fn()}
      />
    );
    const itemElem = screen.getByTestId(`file-${rootItem.fullPath}`);

    act(() => {
      fireEvent.contextMenu(itemElem);
    });

    const menuButton = screen.queryByTestId("file-show-button");
    expect(menuButton).not.toBeTruthy();
  });

  it("has a context menu which interacts with the main process", async () => {
    const rootItem: FileInfo = {
      fullPath: "items/base",
      fileName: "base",
      childrenItems: [
        { fullPath: "items/img.png", fileName: "img.png", childrenItems: [] },
      ],
    };
    render(
      <FileListPane
        rootItem={rootItem}
        selectedPath={"items/img.png"}
        expandedItems={["items/base"]}
        onSelectFileInfo={jest.fn()}
        onRefresh={jest.fn()}
      />
    );

    await act(async () => {
      // Right click the first child item.
      const itemElem = await screen.findByTestId(
        `file-${rootItem.childrenItems[0].fullPath}`
      );
      fireEvent.contextMenu(itemElem);
    });
    expect(screen.queryByTestId("file-show-button")).toBeTruthy();
    expect(mockShowFile).toHaveBeenCalledTimes(0);
    await act(async () => {
      // Click the resulting context menu button to show the file in the windows explorer menu.
      const menuButton = await screen.findByTestId("file-show-button");
      fireEvent.click(menuButton);
    });

    expect(mockShowFile).toHaveBeenCalledTimes(1);
  });
});
