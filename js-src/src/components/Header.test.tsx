import React from "react";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { beforeEach, describe, expect, it, jest } from "@jest/globals";
import FileListPane from "../views/ImageView/components/FileListPane";
import FileInfo from "../types/FileInfo";

jest.mock("../assets/Header.png", () => ({
  __esModule: true,
  default: "",
}));

jest.mock("../utils/mainGateway", () => ({
  MainGateway: {
    showFile: () => { },
  },
}));
import { MainGateway } from "../utils/mainGateway";
import Header from "./Header";

describe("App controls", () => {
  beforeEach(() => {
    const fn = jest.fn();
    render(
      <Header
        goBookTab={fn}
        goGlobalSettingsTab={fn}
        goTextTab={fn}
        goHelpTab={fn}
        goImageTab={fn}
        goWebTab={fn}
        goVideoTab={fn}
        selectedView={"Image"}
      />
    );
  });

  it("uses the gateway to close the app", () => {
    const mockFn = jest.fn();
    MainGateway.closeApp = mockFn;
    const elem = screen.getByTestId("close-app");

    elem.click();

    expect(mockFn).toHaveBeenCalledTimes(1);
  });

  it("uses the gateway to hide the app", () => {
    const mockFn = jest.fn();
    MainGateway.hideApp = mockFn;
    const elem = screen.getByTestId("hide-app");

    elem.click();

    expect(mockFn).toHaveBeenCalledTimes(1);
  });

  it("uses the gateway to expand the app", () => {
    const mockFn = jest.fn();
    MainGateway.expandApp = mockFn;
    const elem = screen.getByTestId("expand-app");

    elem.click();

    expect(mockFn).toHaveBeenCalledTimes(1);
  });
});
