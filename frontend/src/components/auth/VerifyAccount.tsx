import { cn } from "@/lib/utils";
import { Spinner } from "@/components/ui/spinner";
import { useAuthStore } from "@/stores/useAuthStore";
import { useEffect, useRef } from "react";
import { useSearchParams, useNavigate } from "react-router";

export function VerifyAccount({
  className,
  ...props
}: React.ComponentProps<"div">) {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const navigate = useNavigate();
  const hasVerified = useRef(false);

  const { verifyToken, authStatus } = useAuthStore();

  useEffect(() => {
    if (!token || hasVerified.current) return;
    hasVerified.current = true;
    verifyToken(token);
  }, [token, verifyToken]);

  useEffect(() => {
    if (authStatus === "success") {
      navigate("/signin", { replace: true });
    }
  }, [authStatus, navigate]);

  if (authStatus === "loading") {
    return (
      <div className={cn("flex flex-col gap-6", className)} {...props}>
        <Spinner className="size-12 mb-4" />
        <p className="text-lg text-muted-foreground">
          Verifying your account...
        </p>
      </div>
    );
  }

  return null;
}
export default VerifyAccount;
