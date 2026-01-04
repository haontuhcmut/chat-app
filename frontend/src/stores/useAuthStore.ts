import { create } from "zustand";
import { toast } from "sonner";
import { authService } from "@/services/authService";
import type { AuthState } from "@/types/store";

export const useAuthStore = create<AuthState>((set, get) => ({
  accessToken: null,
  user: null,
  loading: false,

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
      toast.success("Registration successful. Please check your email to verify.");
    } catch (error) {
      console.error(error);
      toast.error("Registration failed");
    } finally {
      set({ loading: false });
    }
  },
}));
