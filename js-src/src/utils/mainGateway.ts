const mainGateway = () => {
  const w = window as any;
  return w.electronAPI;
};

export const MainGateway = mainGateway();
