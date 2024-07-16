import { Alert, Snackbar, SnackbarContent } from "@mui/material";
import React, { useState, createContext, useContext, useCallback } from "react";

const AlertContext = createContext((s: string | null) => {});

type AlertProviderProps = {
  children: any;
};

const AlertProvider = ({ children }: AlertProviderProps) => {
  const [message, setMessage] = useState<string | null>(null);

  const handleClose = useCallback(() => setMessage(null), []);

  return (
    <AlertContext.Provider value={setMessage}>
      {children}
      <Snackbar
        open={message !== null}
        autoHideDuration={2500}
        onClose={handleClose}
        anchorOrigin={{ vertical: "top", horizontal: "left" }}
      >
        <Alert severity="success" sx={{ width: "100%" }} onClose={handleClose}>
          {message}
        </Alert>
      </Snackbar>
    </AlertContext.Provider>
  );
};

export const useAlerts = () => {
  const pushAlert = useContext(AlertContext);

  return pushAlert;
};

export default AlertProvider;
