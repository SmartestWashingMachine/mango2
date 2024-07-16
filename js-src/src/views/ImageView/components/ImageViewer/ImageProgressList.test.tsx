import React from "react";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { expect, it, jest } from "@jest/globals";
import ImageProgressList from "./ImageProgressList";

it("should display short text", () => {
  const files = ["Image 1", "Image 2"];
  render(<ImageProgressList curProgress={0} pendingImageNames={files} />);

  expect(screen.getByText(files[0])).toBeTruthy();
  expect(screen.getByText(files[1])).toBeTruthy();
});

it("should cut off long text", () => {
  const files = ["Image 10000000000000000", "Image 2"];
  render(<ImageProgressList curProgress={0} pendingImageNames={files} />);

  expect(screen.queryByText(files[0])).not.toBeTruthy();
  expect(screen.getByText(/Image 1/)).toBeTruthy();
  expect(screen.getByText(files[1])).toBeTruthy();
});

it("should only show first three items", () => {
  const files = ["Image 1", "Image 2", "Image 3", "Image 4", "Image 5"];
  render(<ImageProgressList curProgress={0} pendingImageNames={files} />);

  expect(screen.getByText(files[0])).toBeTruthy();
  expect(screen.getByText(files[1])).toBeTruthy();
  expect(screen.getByText(files[2])).toBeTruthy();
  expect(screen.queryByText(files[3])).not.toBeTruthy();
  expect(screen.queryByText(files[4])).not.toBeTruthy();
  expect(screen.queryByText(/2 more/)).toBeTruthy();
});
