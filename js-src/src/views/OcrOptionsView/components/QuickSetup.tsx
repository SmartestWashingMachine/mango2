import {
  Card,
  Typography,
  CardContent,
  Stack,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Button,
  Link,
  CardActionArea,
} from "@mui/material";
import React from "react";
import BOX_USE_CASES from "../../../utils/boxUseCases";
import { BoxOptions } from "../../../types/BoxOptions";

export type QuickCaseProps = {
  title: string;
  description: string;
  onClick: () => void;
};

const QuickCase = (props: QuickCaseProps) => {
  return (
    <Card>
      <CardActionArea onClick={props.onClick}>
        <CardContent>
          <Typography
            variant="h6"
            sx={{ marginBottom: 1, color: "hsl(291, 3%, 74%)" }}
          >
            {props.title}
          </Typography>
          <Typography variant="body2" sx={{ fontStyle: "italic" }}>
            {props.description}
          </Typography>
        </CardContent>
      </CardActionArea>
    </Card>
  );
};

type QuickSetupConfirmDialogProps = {
  open: boolean;
  selectedCase: any;
  confirmCase: () => void;
  cancelCase: () => void;
};

const QuickSetupConfirmDialog = (props: QuickSetupConfirmDialogProps) => {
  const { open, selectedCase, confirmCase, cancelCase } = props;

  return (
    <Dialog open={open} onClose={cancelCase}>
      <DialogTitle>Confirm Selection</DialogTitle>
      <DialogContent>
        <DialogContentText>
          Switching to a new use case will clear your previous box settings. All
          changes will be lost. Are you sure you want to proceed?
        </DialogContentText>
      </DialogContent>
      <DialogActions>
        <Button onClick={confirmCase} color="primary">
          Confirm
        </Button>
        <Button onClick={cancelCase} color="info">
          Cancel
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export type QuickSetupProps = {
  goAdvancedSettings: () => void;
  setBoxes: (b: BoxOptions[]) => void;
};

const QuickSetup = (props: QuickSetupProps) => {
  const [selectedCase, setSelectedCase] = React.useState<
    (typeof BOX_USE_CASES)[0] | null
  >(null);

  const selectCase = (useCase: any) => {
    setSelectedCase(useCase);
  };

  const confirmCase = () => {
    if (selectedCase) props.setBoxes(selectedCase.options);
    setSelectedCase(null);
  };

  const cancelCase = () => {
    setSelectedCase(null);
  };

  return (
    <Stack spacing={4}>
      <Typography
        variant="h5"
        align="center"
        sx={{ color: "hsl(291, 2%, 88%)" }}
      >
        What's your use case?
      </Typography>
      <Stack spacing={2}>
        {BOX_USE_CASES.map((x) => (
          <QuickCase
            key={x.title}
            description={x.description}
            title={x.title}
            onClick={() => selectCase(x)}
          />
        ))}
      </Stack>
      <Link
        style={{ marginTop: 32 }}
        component="button"
        variant="body2"
        onClick={props.goAdvancedSettings}
      >
        Go to advanced box settings
      </Link>
      <QuickSetupConfirmDialog
        open={selectedCase !== null}
        selectedCase={selectedCase}
        confirmCase={confirmCase}
        cancelCase={cancelCase}
      />
    </Stack>
  );
};

export default QuickSetup;
