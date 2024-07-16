import React from "react";
import { faker } from "@faker-js/faker";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { expect, it, jest } from "@jest/globals";
import KeySelect from "./KeySelect";

it("should show ESCAPE key as DISABLED", () => {
  render(
    <KeySelect
      onKeyChange={jest.fn()}
      value="Escape"
      label="label"
      tooltip="tooltip"
    />
  );

  expect(screen.getByDisplayValue(/DISABLED/));
});

it("should show k key as k", () => {
  render(
    <KeySelect
      onKeyChange={jest.fn()}
      value="k"
      label="label"
      tooltip="tooltip"
    />
  );

  expect(screen.getByDisplayValue("k")).toBeTruthy();
});

it("should allow single alphabetic character", () => {
  const letter = faker.string.alpha(1).toLowerCase();
  const initialLetter = "Q";
  const mockFn = jest.fn();
  render(
    <KeySelect
      onKeyChange={mockFn}
      value={initialLetter}
      label="label"
      tooltip="tooltip"
    />
  );

  act(() => {
    const elem = screen.getByDisplayValue(initialLetter);
    fireEvent.keyDown(elem, { key: letter });
  });

  expect(screen.queryByDisplayValue(initialLetter)).not.toBeTruthy();
  expect(screen.getByDisplayValue(letter)).toBeTruthy();
  expect(mockFn).toHaveBeenCalledTimes(1);
});

it("should not allow single alphanumeric character", () => {
  const letter = faker.string.numeric(1).toLowerCase();
  const initialLetter = "x";
  const mockFn = jest.fn();
  render(
    <KeySelect
      onKeyChange={mockFn}
      value={initialLetter}
      label="label"
      tooltip="tooltip"
    />
  );

  act(() => {
    const elem = screen.getByDisplayValue(initialLetter);
    fireEvent.keyDown(elem, { key: letter });
  });

  expect(screen.getByDisplayValue(initialLetter)).toBeTruthy();
  expect(screen.queryByDisplayValue(letter)).not.toBeTruthy();
  expect(mockFn).toHaveBeenCalledTimes(0);
});

it("should allow uppercase alphabetic character", () => {
  const letter = faker.string.alpha(1).toUpperCase();
  const initialLetter = "l";
  const mockFn = jest.fn();
  render(
    <KeySelect
      onKeyChange={mockFn}
      value={initialLetter}
      label="label"
      tooltip="tooltip"
    />
  );

  act(() => {
    const elem = screen.getByDisplayValue(initialLetter);
    fireEvent.keyDown(elem, { key: letter });
  });

  expect(screen.queryByDisplayValue(initialLetter)).not.toBeTruthy();
  expect(screen.getByDisplayValue(letter)).toBeTruthy();
  expect(mockFn).toHaveBeenCalledTimes(1);
});

it("should not allow a key of length 2", () => {
  const letter = faker.string.alpha(2);
  const initialLetter = "l";
  const mockFn = jest.fn();
  render(
    <KeySelect
      onKeyChange={mockFn}
      value={initialLetter}
      label="label"
      tooltip="tooltip"
    />
  );

  act(() => {
    const elem = screen.getByDisplayValue(initialLetter);
    fireEvent.keyDown(elem, { key: letter });
  });

  expect(screen.getByDisplayValue(initialLetter)).toBeTruthy();
  expect(screen.queryByDisplayValue(letter)).not.toBeTruthy();
  expect(mockFn).toHaveBeenCalledTimes(0);
});
