export const debugListeners = async () => {
  const w = window as any;

  const listenerNames = await w.electronAPI.getListenerNames();
  console.log(`DEBUG Listeners: ${JSON.stringify(listenerNames)}`);
};
