import { Spinner } from "@/components/ui/spinner";
import { useAuthStore } from "@/stores/useAuthStore";
import { useEffect, useRef } from "react";
import { useSearchParams, useNavigate } from "react-router";

const VerifyAccount = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const navigate = useNavigate();
  const hasVerified = useRef(false); // ← ADD THIS

  const { verifyToken, verifyAccountStatus } = useAuthStore();

  useEffect(() => {
    if (!token || hasVerified.current) return; // ← PREVENTS 2ND CALL
    hasVerified.current = true;
    verifyToken(token);
  }, [token, verifyToken]);

  useEffect(() => {
    if (verifyAccountStatus === "success") {
      navigate("/signin", { replace: true });
    }
  }, [verifyAccountStatus, navigate]);

  if (verifyAccountStatus === "loading") {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center p-8">
        <Spinner className="size-12 mb-4" />
        <p className="text-lg text-muted-foreground">
          Verifying your account...
        </p>
      </div>
    );
  }

  return null; // ← SIMPLER: no empty div
};
export default VerifyAccount;
