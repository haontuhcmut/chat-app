import { create } from "zustand";
import { authService } from "@/services/authService";
import type { SocketState } from "@/types/store";
import { useAuthStore } from "./useAuthStore";

const baseURL = import.meta.env.VITE_SOCKET_URL;

export const useSocketStore = create<SocketState>((set, get) => ({
  socket: null,

  onlineUsers: [],

  connectSocket: () => {
    const accessToken = useAuthStore.getState().accessToken;
    const existingSocket = get().socket;

    if (existingSocket) return;

    const ws = new WebSocket(`${baseURL}/?token=${accessToken}`);

    ws.onopen = () => {
      console.log("Websocket connected");
    };

    ws.onmessage = (event) => {
      console.log("RAW:", event.data);
      const data = JSON.parse(event.data);

      if (data.type === "presence") {
        const { client_id, status } = data;

        set((state) => {
          const isOnline = state.onlineUsers.includes(client_id);

          if (status === "online" && !isOnline) {
            return {
              onlineUsers: [...state.onlineUsers, client_id],
            };
          }

          if (status === "offline" && isOnline) {
            return {
              onlineUsers: state.onlineUsers.filter((id) => id !== client_id),
            };
          }

          return state;
        });
      }
    };
  },

  disconnectSocket: () => {
    const socket = get().socket;

    if (socket) {
      socket.close();
      set({ socket: null });
    }
  },
}));
