import type { User } from "./user";

export type VerifyAccountStatus = "idle" | "loading" | "success" | "error";

export interface AuthState {
  accessToken: string | null;
  user: User | null;
  loading: boolean;

  verifyAccountStatus: VerifyAccountStatus;

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
}
