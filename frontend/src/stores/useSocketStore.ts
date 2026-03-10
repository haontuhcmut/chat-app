import { create } from "zustand";
import { authService } from "@/services/authService";
import type { SocketState } from "@/types/store";

const baseURL = import.meta.env.VITE_SOCKET_URL;

export const useSocketStore = create<SocketState>((set, get) => ({
  socket: null,
  onlineUsers: [],
  connectSocket: async () => {
    const existingSocket = get().socket;

    if (existingSocket) return;

    const sid = await authService.wsSession();
    const ws = new WebSocket(`${baseURL}?sid=${sid}`);
    ws.onopen = () => {
      console.log("Websocket connected");
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "online_users") {
        set({
          onlineUsers: data.users,
        });
      }

      if (data.type === "presence") {
        if (data.status === "online") {
          set((state) => {
            if (state.onlineUsers.includes(data._id)) return state;

            return {
              onlineUsers: [...state.onlineUsers, data._id],
            };
          });
        }

        if (data.status === "offline") {
          set((state) => ({
            onlineUsers: state.onlineUsers.filter((id) => id !== data._id),
          }));
        }
      }
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
