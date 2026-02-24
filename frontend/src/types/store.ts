import type { User } from "./user";
import type { Conversation, Message } from "./chat";

export type authStatus = "idle" | "loading" | "success" | "error";

export interface AuthState {
  accessToken: string | null;
  user: User | null;
  loading: boolean;
  authStatus: authStatus;

  setAccessToken: (accessToken: string) => void;

  clearState: () => void;

  signUp: (
    username: string,
    password: string,
    email: string,
    fristName: string,
    lastName: string,
    confirmPassowrd: string,
  ) => Promise<void>;

  verifyToken: (token: string) => Promise<void>;

  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  fetchMe: () => Promise<void>;
  refresh: () => Promise<void>;
}

export interface ThemeState {
  isDark: boolean;
  toggleTheme: () => void;
  setTheme: (dark: boolean) => void;
}

export interface ChatState {
  conversations: Conversation[];
  messages: Record<
    string,
    {
      items: Message[];
      hasMore: boolean; // infinite-scroll
      nextCursor?: string | null; // pagination
    }
  >;
  activeConversationId: string | null;
  convoLoading: boolean;
  messageLoading: boolean;
  reset: () => void;

  setActiveConversation: (id: string | null) => void;
  fetchConversations: () => Promise<void>;
  fetchMessages: (conversationId?: string) => Promise<void>;
}
