import React from "react";
import { faker } from "@faker-js/faker";
import { render, screen } from "@testing-library/react";
import { expect, it } from "@jest/globals";
import BaseHelp from "./BaseHelp";

const range = (n: number) => [...Array(n).keys()];

it("shows each step", async () => {
  const steps = range(faker.number.int({ min: 1, max: 20 })).map((_) =>
    faker.string.alphanumeric({ length: { min: 1, max: 400 } })
  );
  render(<BaseHelp title="blah" steps={steps} />);

  for (const st of steps) {
    expect(screen.getByText(st)).toBeTruthy();
  }
});
