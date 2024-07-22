import { io, ManagerOptions, SocketOptions } from "socket.io-client";
import { MainGateway } from "../utils/mainGateway";

export const makeSocket = (opts?: any) => {
  const listeners: any[] = [];

  return {
    listeners,
    on: (eventName: string, cb: (...args: any[]) => void) => {
      const lis = MainGateway.bridgeOn(eventName, (e: any, ...a: any[]) => {
        cb(...a);
      });

      listeners.push(lis);

      if (eventName === 'connect') cb();
    },
    disconnect: () => {
      for (const lis of listeners) {
        lis();
      }
    },
  };
};
