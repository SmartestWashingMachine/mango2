import { Grid } from "@mui/material";
import React from "react";

type BaseViewProps = {
  children: any;
  rightPane?: any;
  noPadding?: boolean;
  leftXs?: number;
  rightXs?: number;
  noHeight?: boolean;
};

const BaseView = ({
  children,
  rightPane,
  noPadding,
  leftXs,
  rightXs,
  noHeight,
}: BaseViewProps) => {
  return (
    <Grid container className={noPadding ? "" : "appContainer"} id="base-view">
      <Grid
        item
        xs={!!rightPane ? leftXs || 9 : 12}
        className={noHeight ? "appContainerLeftNoHeight" : "appContainerLeft"}
      >
        {children}
      </Grid>
      {!!rightPane && (
        <Grid
          item
          xs={rightXs || 3}
          className={
            noHeight ? "appContainerRightNoHeight" : "appContainerRight"
          }
        >
          {rightPane}
        </Grid>
      )}
    </Grid>
  );
};

export default BaseView;
