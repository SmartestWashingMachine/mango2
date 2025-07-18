import { ThemeProvider } from "@emotion/react";
import { Box, CssBaseline, createTheme } from "@mui/material";
import React from "react";
import HomePage from "./HomePage";
import HomeVideoPage from "./HomeVideoPage";
import { indigo } from "@mui/material/colors";
import AlertProvider from "../components/AlertProvider";

const theme = createTheme({
  palette: {
    contrastThreshold: 4.5,
    mode: "dark",
    background: {
      default: "hsl(291, 9%, 13%)",
      paper: "hsl(291, 12%, 10%)",
    },
    primary: {
      //...purple,
      main: "#ce93d8",
      600: "#8e24aa",
      700: "#7b1fa2",
    },
    secondary: indigo,
    info: {
      100: "hsl(291, 1%, 96%)",
      200: "hsl(291, 1%, 93%)",
      300: "hsl(291, 2%, 88%)",
      400: "hsl(291, 3%, 74%)",
      500: "hsl(291, 3%, 62%)",
      600: "hsl(291, 4%, 46%)",
      700: "hsl(291, 6%, 38%)",
      800: "hsl(291, 8%, 26%)",
      900: "hsl(291, 10%, 13%)",
    },
  },
});

const queryParams = new URLSearchParams(window.location.search);
const mediaParam = queryParams.get("media");

const WebApp = () => {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline>
        <AlertProvider>
          <Box sx={{ display: "flex", flexDirection: "column" }}>
            {mediaParam === "video" && <HomeVideoPage />}
            {mediaParam !== "video" && <HomePage />}
          </Box>
        </AlertProvider>
      </CssBaseline>
    </ThemeProvider>
  );
};

export default WebApp;
