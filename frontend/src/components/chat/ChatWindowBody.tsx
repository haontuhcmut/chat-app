import { useChatStore } from "@/stores/useChatStore";
import React from "react";
import ChatWelcomeScreen from "./ChatWelcomeScreen";

const ChatWindowBody = () => {
  const {
    activeConversationId,
    conversations,
    messages: allMessages,
  } = useChatStore();

  const messages = allMessages[activeConversationId!]?.items ?? [];
  const selectedConvo = conversations.find(
    (c) => c._id === activeConversationId,
  );

  if (!selectedConvo) {
    return <ChatWelcomeScreen />;
  }

  if (!messages?.length) {
    return (
      <div className="flex h-full item-center justify-center text-muted-foreground">
        There isn't any message in this conversation.
      </div>
    );
  }

  return (
    <div className="p-4 bg-primary-foreground h-full flex flex-col overflow-hidden">
      <div className="flex flex-col overflow-y-auto overflow-x-hidden beautiful-scrollbar">
        {messages.map((message) => (
          <>{message.content}</>
        ))}
      </div>
    </div>
  );
};

export default ChatWindowBody;
