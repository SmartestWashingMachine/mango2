import { io, ManagerOptions, SocketOptions } from "socket.io-client";

export const makeSocket = (opts?: Partial<SocketOptions | ManagerOptions>) =>
  io("ws://127.0.0.1:5000", { ackTimeout: 100000, transports: ['websocket'], ...opts, });
