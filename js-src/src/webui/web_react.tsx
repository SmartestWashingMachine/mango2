import * as React from "react";
import * as ReactDOM from "react-dom";
import { createRoot } from "react-dom/client";
import "./webui_styles.css";
import WebApp from "./WebApp";

const container = document.getElementById("react-app");
const root = createRoot(container!);

root.render(<WebApp />);
