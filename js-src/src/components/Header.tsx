import {
  AppBar,
  Box,
  Button,
  IconButton,
  Stack,
  Toolbar,
  Typography,
} from "@mui/material";
import React, { useState } from "react";
import MinimizeIcon from "@mui/icons-material/Remove";
import CloseIcon from "@mui/icons-material/Close";
import FullscreenIcon from "@mui/icons-material/Fullscreen";
import Views from "../types/Views";
import { useLoader } from "./LoaderContext";
import path from "path";
import { app } from "electron";
import MenuIcon from "@mui/icons-material/Menu";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";

import HeaderPng from "../assets/Header.png";
import { MainGateway } from "../utils/mainGateway";

const btnSize = "small";

type HeaderProps = {
  goTextTab: () => void;
  goImageTab: () => void;
  goBookTab: () => void;
  goGlobalSettingsTab: () => void;
  goHelpTab: () => void;
  goWebTab: () => void;
  goVideoTab: () => void;
  selectedView: Views | null;
};

const Header = ({
  goTextTab,
  goImageTab,
  goBookTab,
  goGlobalSettingsTab,
  goHelpTab,
  goWebTab,
  goVideoTab,
  selectedView,
}: HeaderProps) => {
  const { loading } = useLoader();

  const [anchorElNav, setAnchorElNav] = useState<null | HTMLElement>(null);

  const handleOpenNavMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorElNav(event.currentTarget);
  };

  const handleCloseNavMenu = () => {
    setAnchorElNav(null);
  };

  const closeApp = () => {
    MainGateway.closeApp();
  };

  const hideApp = () => {
    MainGateway.hideApp();
  };

  const expandApp = () => {
    MainGateway.expandApp();
  };

  return (
    <AppBar component="nav" position="sticky" className="header">
      <Toolbar variant="dense">
        <Stack
          sx={{
            flexGrow: 1,
            alignItems: "center",
            display: { xs: "none", md: "flex" },
          }}
          spacing={2}
          direction="row"
        >
          <div className="logoImgContainer">
            <img src={HeaderPng} className="logoImg" alt="Mango" />
          </div>
          <Button
            sx={{
              color: selectedView == "Text" ? "white" : "hsl(291, 3%, 74%)",
            }}
            onClick={goTextTab}
            disabled={loading}
            size={btnSize}
          >
            Text
          </Button>
          <Button
            sx={{
              color: selectedView == "Image" ? "white" : "hsl(291, 3%, 74%)",
            }}
            onClick={goImageTab}
            disabled={loading}
            size={btnSize}
          >
            Images
          </Button>
          <Button
            sx={{
              color: selectedView == "Book" ? "white" : "hsl(291, 3%, 74%)",
            }}
            onClick={goBookTab}
            disabled={loading}
            size={btnSize}
          >
            Book
          </Button>
          <Button
            sx={{
              color:
                selectedView == "GlobalSettings"
                  ? "white"
                  : "hsl(291, 3%, 74%)",
            }}
            onClick={goGlobalSettingsTab}
            disabled={loading}
            size={btnSize}
          >
            Settings
          </Button>
          <Button
            sx={{
              color: selectedView == "Web" ? "white" : "hsl(291, 3%, 74%)",
            }}
            onClick={goWebTab}
            disabled={loading}
            size={btnSize}
          >
            Web
          </Button>
          <Button
            sx={{
              color: selectedView == "Video" ? "white" : "hsl(291, 3%, 74%)",
            }}
            onClick={goVideoTab}
            disabled={loading}
            size={btnSize}
          >
            Video
          </Button>
          <Button
            sx={{
              color: "hsl(291, 3%, 74%)",
            }}
            onClick={goHelpTab}
            // disabled={loading}
            size={btnSize}
          >
            Help
          </Button>
        </Stack>
        <Box
          className="logoImgContainer"
          sx={{ display: { xs: "block", md: "none" } }}
        >
          <img src={HeaderPng} className="logoImg" alt="Mango" />
        </Box>
        <Box
          sx={{
            flexGrow: 1,
            display: { xs: "flex", md: "none" },
            flexDirection: "row-reverse",
            mr: 2,
          }}
        >
          <IconButton size="large" onClick={handleOpenNavMenu} color="inherit">
            <MenuIcon />
          </IconButton>
          <Menu
            anchorEl={anchorElNav}
            anchorOrigin={{
              vertical: "bottom",
              horizontal: "left",
            }}
            keepMounted
            transformOrigin={{
              vertical: "top",
              horizontal: "left",
            }}
            open={!!anchorElNav}
            onClose={handleCloseNavMenu}
            sx={{
              display: { xs: "block", md: "none" },
            }}
          >
            <MenuItem
              onClick={() => {
                handleCloseNavMenu();
                goTextTab();
              }}
              sx={{
                color: selectedView == "Text" ? "white" : "hsl(291, 3%, 74%)",
              }}
              disabled={loading}
            >
              <Typography textAlign="center">Text</Typography>
            </MenuItem>
            <MenuItem
              onClick={() => {
                handleCloseNavMenu();
                goImageTab();
              }}
              sx={{
                color: selectedView == "Image" ? "white" : "hsl(291, 3%, 74%)",
              }}
              disabled={loading}
            >
              <Typography textAlign="center">Images</Typography>
            </MenuItem>
            <MenuItem
              onClick={() => {
                handleCloseNavMenu();
                goBookTab();
              }}
              sx={{
                color: selectedView == "Book" ? "white" : "hsl(291, 3%, 74%)",
              }}
              disabled={loading}
            >
              <Typography textAlign="center">Book</Typography>
            </MenuItem>
            <MenuItem
              onClick={() => {
                handleCloseNavMenu();
                goGlobalSettingsTab();
              }}
              sx={{
                color:
                  selectedView == "GlobalSettings"
                    ? "white"
                    : "hsl(291, 3%, 74%)",
              }}
              disabled={loading}
            >
              <Typography textAlign="center">Settings</Typography>
            </MenuItem>
            <MenuItem
              onClick={() => {
                handleCloseNavMenu();
                goWebTab();
              }}
              sx={{
                color: selectedView == "Web" ? "white" : "hsl(291, 3%, 74%)",
              }}
              disabled={loading}
            >
              <Typography textAlign="center">Web</Typography>
            </MenuItem>
            <MenuItem
              onClick={() => {
                handleCloseNavMenu();
                goVideoTab();
              }}
              sx={{
                color: selectedView == "Video" ? "white" : "hsl(291, 3%, 74%)",
              }}
              disabled={loading}
            >
              <Typography textAlign="center">Video</Typography>
            </MenuItem>
            <MenuItem
              onClick={() => {
                handleCloseNavMenu();
                goHelpTab();
              }}
              sx={{
                color: "hsl(291, 3%, 74%)",
              }}
              disabled={loading}
            >
              <Typography textAlign="center">Help</Typography>
            </MenuItem>
          </Menu>
        </Box>
        <IconButton onClick={hideApp} data-testid="hide-app">
          <MinimizeIcon />
        </IconButton>
        <IconButton onClick={expandApp} data-testid="expand-app">
          <FullscreenIcon />
        </IconButton>
        <IconButton onClick={closeApp} data-testid="close-app">
          <CloseIcon />
        </IconButton>
      </Toolbar>
    </AppBar>
  );
};

export default Header;
