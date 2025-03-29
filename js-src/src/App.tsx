import { Box, CssBaseline, ThemeProvider } from "@mui/material";
import React, { useEffect, useRef, useState } from "react";
import Views from "./types/Views";
import "./styles/App.css";
import TextView from "./views/TextView/TextView";
import ImageView from "./views/ImageView/ImageView";
import OptionsView from "./views/OcrOptionsView/OptionsView";
import Header from "./components/Header";
import WebView from "./views/WebView";
import BookView from "./views/BookView";
import VideoView from "./views/VideoView";
import { CSSTransition, SwitchTransition } from "react-transition-group";
import LoaderContext from "./components/LoaderContext";
import GlobalOptionsView from "./views/GlobalOptionsView/GlobalOptionsView";
import AlertProvider from "./components/AlertProvider";
import { MainGateway } from "./utils/mainGateway";
import { appTheme } from "./appTheme";
import ImageViewModeProvider from "./components/ImageViewModeProvider";

const transitionTimeouts = {
  enter: 300,
  exit: 300,
};

const App = () => {
  const [curView, setCurView] = useState<Views | null>(null);
  const nodeRef = useRef<any | null>(null);

  const [loading, setLoading] = useState(false);

  const selTextTab = () => {
    setCurView("Text");
  };

  const selImageTab = () => {
    setCurView("Image");
  };

  const selWebTab = () => {
    setCurView("Web");
  };

  const selBookTab = () => {
    setCurView("Book");
  };

  const selSettingsTab = () => {
    setCurView("Box Settings");
  };

  const selGlobalSettingsTab = () => {
    setCurView("Model Settings");
  };

  const selVideoTab = () => {
    setCurView("Video");
  };

  const selHelpTab = () => {
    MainGateway.openHelpWindow();
  };

  useEffect(() => {
    if (!curView) return;

    MainGateway.setStoreValue("currentView", curView);
  }, [curView]);

  useEffect(() => {
    let canceled = false;

    const asyncCb = async () => {
      const data = await MainGateway.getStoreData();

      if (canceled) return;
      setCurView(data.currentView);
    };

    asyncCb();

    return () => {
      canceled = true;
    };
  }, []);

  return (
    <LoaderContext.Provider value={{ loading, setLoading }}>
      <ThemeProvider theme={appTheme}>
        <CssBaseline>
          <Box sx={{ display: "flex", flexDirection: "column" }}>
            <Header
              selectedView={curView}
              goImageTab={selImageTab}
              goTextTab={selTextTab}
              goGlobalSettingsTab={selGlobalSettingsTab}
              goBookTab={selBookTab}
              goHelpTab={selHelpTab}
              goWebTab={selWebTab}
              goVideoTab={selVideoTab}
            />
            <div className="appRootContainer">
              <SwitchTransition mode="out-in">
                <CSSTransition
                  key={curView}
                  nodeRef={nodeRef}
                  unmountOnExit
                  timeout={transitionTimeouts}
                  classNames="page"
                >
                  <div className="appRootInnerContainer" ref={nodeRef}>
                    <AlertProvider>
                      {curView === "Text" && (
                        <TextView onOpenOcrSettings={selSettingsTab} />
                      )}
                      {curView === "Image" && (
                        <ImageViewModeProvider>
                          <ImageView />
                        </ImageViewModeProvider>
                      )}
                      {curView === "Book" && <BookView />}
                      {curView === "Box Settings" && (
                        <OptionsView goTextTab={selTextTab} />
                      )}
                      {curView === "Model Settings" && (
                        <GlobalOptionsView goOcrOptionsTab={selSettingsTab} />
                      )}
                      {curView === "Web" && <WebView />}
                      {curView === "Video" && <VideoView />}
                    </AlertProvider>
                  </div>
                </CSSTransition>
              </SwitchTransition>
            </div>
          </Box>
        </CssBaseline>
      </ThemeProvider>
    </LoaderContext.Provider>
  );
};

export default App;
