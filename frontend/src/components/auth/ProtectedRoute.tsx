import { useAuthStore } from "@/stores/useAuthStore";
import { Navigate, Outlet } from "react-router";

const ProtectedRoute = () => {
  const { accessToken, user, loading } = useAuthStore();

  if (!accessToken) {
    return <Navigate to="/signin" replace></Navigate>;
  }

  return <Outlet></Outlet>;
};

export default ProtectedRoute;
