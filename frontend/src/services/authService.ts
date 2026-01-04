import api from "@/lib/axios";

export const authService = {
  signUp: async (
    username: string,
    password: string,
    email: string,
    first_name: string,
    last_name: string,
    confirm_password: string
  ) => {
    const res = await api.post(
      "auth/signup",
      { username, password, email, first_name, last_name, confirm_password },
      { withCredentials: true }
    );
    return res.data;
  },

  verifyAccount: async (token: string) => {
    const res = await api.get(`auth/verify/${token}`, {
      withCredentials: true,
    });
    return res.data;
  },
};
