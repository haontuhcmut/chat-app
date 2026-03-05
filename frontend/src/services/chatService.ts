import api from "@/lib/axios";
import type { ConversationResponse, Message } from "@/types/chat";

interface FetchMessageProps {
  messages: Message[];
  cursor?: string;
}

const pageLimit = 50;

export const chatService = {
  async fetchConversations(): Promise<ConversationResponse> {
    const res = await api.get("/conversations/");
    return res.data;
  },

  async fetchMessages(id: string, cursor?: string) {
    const res = await api.get(`/conversations/${id}/messages`, {
      params: {
        limit: pageLimit,
        ...(cursor ? { cursor } : {}),
      },
    });

    return {
      messages: res.data.messages,
      cursor: res.data.nextCursor,
    };
  },

  async sendDirectMessage(
    recipient_id: string,
    content: string = "",
    img_url?: string,
    conv_id?: string,
  ) {
    const res = await api.post("/messages/direct", {
      content,
      img_url,
      recipient_id,
      conv_id,
    });
    return res.data.content;
  },

  async sendGroupMessage(
    conv_id: string,
    content: string = "",
    img_url?: string,
  ) {
    const res = await api.post("/messages/group", {
      conv_id,
      content,
      img_url,
    });
    return res.data.content;
  },
};
