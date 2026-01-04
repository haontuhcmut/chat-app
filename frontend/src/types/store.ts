import type { User } from "./user";

export interface AuthState {
  accessToken: string | null;
  user: User | null;
  loading: boolean;

  signUp: (
    username: string,
    password: string,
    email: string,
    fristName: string,
    lastName: string,
    confirmPassowrd: string
  ) => Promise<void>;
}
