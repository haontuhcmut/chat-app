import { create } from "zustand";
import { toast } from "sonner";
import { authService } from "@/services/authService";
import type { AuthState } from "@/types/store";

export const useAuthStore = create<AuthState>((set, get) => ({
  accessToken: null,
  user: null,
  loading: false,
  authStatus: "idle",

  clearState: () => {
    set({ accessToken: null, user: null, loading: false });
  },

  signUp: async (
    username,
    password,
    email,
    firstName,
    lastName,
    confirmPassowrd
  ) => {
    try {
      set({ loading: true });

      await authService.signUp(
        username,
        password,
        email,
        firstName,
        lastName,
        confirmPassowrd
      );
      toast.success(
        "Registration successful. Please check your email to verify."
      );
    } catch (error) {
      console.error(error);
      toast.error("Registration failed");
    } finally {
      set({ loading: false });
    }
  },
  verifyToken: async (token: string) => {
    set({ loading: true, status: "loading" });
    try {
      await authService.verifyToken(token);
      set({ authStatus: "success" });
      toast.success(
        "Account successfully verified. Please go to sign in page."
      );
    } catch (error) {
      console.error(error);
      set({ authStatus: "error" });
      toast.error("Verification link is invalid. Please try again!");
    } finally {
      set({ loading: false });
    }
  },

  signIn: async (email, password) => {
    try {
      set({ loading: true });

      const { access_token } = await authService.signIn(email, password);

      set({ accessToken: access_token });

      await get().fetchMe();

      toast.success("Welcome back!");
    } catch (error) {
      console.error(error);
      toast.error("Sign in failed!");
    } finally {
      set({ loading: false });
    }
  },

  signOut: async () => {
    try {
      await authService.signOut();
      get().clearState();
      toast.success("You've been signed out");
    } catch (error) {
      toast.error("An error occurred during sign-out. Please try again.");
    }
  },

  fetchMe: async () => {
    try {
      set({ loading: true });
      const user = await authService.fetchMe();
      set({ user: user });
    } catch (error) {
      console.error(error);
      set({ accessToken: null, user: null });
      toast.error("Failed fetch user. Please try again!");
    } finally {
      set({ loading: false });
    }
  },
}));
