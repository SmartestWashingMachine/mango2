import { Grid } from "@mui/material";
import React from "react";

type BaseViewProps = {
  children: any;
  rightPane?: any;
  noPadding?: boolean;
};

const BaseView = ({ children, rightPane, noPadding }: BaseViewProps) => {
  return (
    <Grid container className={noPadding ? "" : "appContainer"} id="base-view">
      <Grid item xs={!!rightPane ? 9 : 12} className="appContainerLeft">
        {children}
      </Grid>
      {!!rightPane && (
        <Grid item xs={3} className="appContainerRight">
          {rightPane}
        </Grid>
      )}
    </Grid>
  );
};

export default BaseView;
