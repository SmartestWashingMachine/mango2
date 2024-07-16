import React from "react";
import { render, screen, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { it, jest, expect } from "@jest/globals";
import ImageFolderInputDialog from "./ImageFolderInputDialog";
import FileInfo from "../../../types/FileInfo";

it("should display a warning if typing in the name of an existing folder", async () => {
  const rootItem: FileInfo = {
    fullPath: "",
    fileName: "",
    childrenItems: [
      {
        fullPath: "sample/samplename",
        fileName: "samplename",
        childrenItems: [],
      },
    ],
  };
  userEvent.setup();
  render(
    <ImageFolderInputDialog
      onDone={jest.fn()}
      onClose={jest.fn()}
      open
      rootItem={rootItem}
    />
  );
  const inp = screen.getByRole("textbox");

  await act(async () => {
    // MUI TextField does not play nice with fireEvent.
    await userEvent.type(inp, rootItem.childrenItems[0].fileName);
  });

  expect(screen.getByText("This folder already exists.")).toBeTruthy();
});

it("should display a warning if typing in the name of a folder that does exist but in different casing", async () => {
  const rootItem: FileInfo = {
    fullPath: "",
    fileName: "",
    childrenItems: [
      {
        fullPath: "alf/abcd",
        fileName: "abcd",
        childrenItems: [],
      },
    ],
  };
  userEvent.setup();
  render(
    <ImageFolderInputDialog
      onDone={jest.fn()}
      onClose={jest.fn()}
      open
      rootItem={rootItem}
    />
  );
  const inp = screen.getByRole("textbox");

  await act(async () => {
    await userEvent.type(inp, rootItem.childrenItems[0].fileName.toUpperCase());
  });

  expect(screen.getByText("This folder already exists.")).toBeTruthy();
});

it("should not display a warning if typing in the name of a folder that does not exist", async () => {
  const rootItem: FileInfo = {
    fullPath: "",
    fileName: "",
    childrenItems: [
      {
        fullPath: "alf/abcd",
        fileName: "abcd",
        childrenItems: [],
      },
    ],
  };
  userEvent.setup();
  render(
    <ImageFolderInputDialog
      onDone={jest.fn()}
      onClose={jest.fn()}
      open
      rootItem={rootItem}
    />
  );
  const inp = screen.getByRole("textbox");

  await act(async () => {
    await userEvent.type(inp, "defg");
  });

  expect(screen.queryByText("This folder already exists.")).not.toBeTruthy();
});

it("should not display a warning if typing in the name of a folder that does not exist in the root folder itself", async () => {
  const rootItem: FileInfo = {
    fullPath: "",
    fileName: "",
    childrenItems: [
      {
        fullPath: "alf/abcd",
        fileName: "abcd",
        childrenItems: [
          {
            fullPath: "alf/abcd/nesteditem",
            fileName: "nesteditem",
            childrenItems: [],
          },
        ],
      },
    ],
  };
  userEvent.setup();
  render(
    <ImageFolderInputDialog
      onDone={jest.fn()}
      onClose={jest.fn()}
      open
      rootItem={rootItem}
    />
  );
  const inp = screen.getByRole("textbox");

  await act(async () => {
    await userEvent.type(
      inp,
      rootItem.childrenItems[0].childrenItems[0].fileName
    );
  });

  expect(screen.queryByText("This folder already exists.")).not.toBeTruthy();
});
