import React from "react";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { beforeEach, describe, expect, it, jest } from "@jest/globals";
import HistoryPane from "./HistoryPane";
import IHistoryText from "../../../types/HistoryText";

it("should show an empty message when no texts are given", () => {
  render(<HistoryPane texts={[]} selectedIds={[]} onSelectItem={jest.fn()} />);

  const elem = screen.queryByText("Backlog empty.");
  expect(elem).toBeTruthy();
});

it("should show an item when a text is given", () => {
  const stubTexts: IHistoryText[] = [
    {
      sourceText: "abc",
      targetText: ["def"],
      sourceTokens: [],
      targetTokens: [],
      uuid: "a",
      attentions: [],
      otherTargetTexts: [],
    },
  ];
  render(
    <HistoryPane
      texts={stubTexts}
      selectedIds={[]}
      onSelectItem={jest.fn()}
      initialItemCount={1}
    />
  );

  const elem = screen.queryByText("Backlog empty.");
  expect(elem).not.toBeTruthy();
  expect(screen.getByText(stubTexts[0].sourceText)).toBeTruthy();
  expect(screen.getByText(stubTexts[0].targetText[0])).toBeTruthy();
});
