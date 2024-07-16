import { createTheme } from "@mui/material";
import { indigo } from "@mui/material/colors";

export const appTheme = createTheme({
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
