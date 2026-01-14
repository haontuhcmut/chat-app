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

  verifyToken: async (token: string) => {
    const res = await api.get(`auth/verify/${token}`, {
      withCredentials: true,
    });
    return res.data;
  },

  signIn: async (email: string, password: string) => {
    const data = new URLSearchParams();
    data.append("username", email);
    data.append("password", password);

    const res = await api.post("auth/signin", data, {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      withCredentials: true,
    });
    return res.data;
  },

  signOut: async () => {
    return api.post("auth/signout", null, {
      withCredentials: true,
    });
  },

  fetchMe: async () => {
    const res = await api.get("auth/me", { withCredentials: true });
    return res.data;
  },

  refresh: async () => {
    const res = await api.post("/auth/refresh", { withCredentials: true });
    return res.data.access_token;
  },
};
