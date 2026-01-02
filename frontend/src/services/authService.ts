import api from "@/lib/axios";

interface SignUpPayload {
  username: string;
  password: string;
  confirm_password: string;
  email: string;
  firstName: string;
  lastName: string;
}

export const authService = {
  signUp: async (payload: SignUpPayload) => {
    const res = await api.post(
      "/auth/signup",
      payload,
      { withCredentials: true }
    );

    return res.data;
  },
};
