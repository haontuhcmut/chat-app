import type { User } from "./user";

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
    confirmPassowrd: string
  ) => Promise<void>;

  verifyToken: (token: string) => Promise<void>;

  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  fetchMe: () => Promise<void>;
  refresh: () => Promise<void>;
}
