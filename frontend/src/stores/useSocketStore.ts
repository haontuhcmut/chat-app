import { create } from "zustand";
import { useAuthStore } from "./useAuthStore";
import { authService } from "@/services/authService";
import type { SocketState } from "@/types/store";

const baseURL = import.meta.env.VITE_SOCKET_URL;

export const useSocketStore = create<SocketState>((set, get) => ({
  socket: null,
  connectSocket: async () => {
    const existingSocket = get().socket;

    if (existingSocket) return;
    const sid = await authService.wsSession();
    const ws = new WebSocket(`${baseURL}?sid=${sid}`);
    ws.onopen = () => {
      console.log("Websocket connected");
    };

    set({ socket: ws });
  },
  disconectSocket: () => {
    const socket = get().socket;

    if (socket) {
      socket.close();
      set({ socket: null });
    }
  },
}));
