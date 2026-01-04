import { authService } from "@/services/authService";
import { use, useEffect, useState } from "react";
import { useSearchParams } from "react-router";

export const VerifyAccountPage = () => {
  const [sharcj] = useSearchParams();
  const [loading, setLoading] = useState(false);
  const [isError, setIsError] = useState(false);

  const token = sharcj.get("token");

  const callAPI = async () => {
    setLoading(true);
    if (token) {
      try {
        await authService.verifyAccount(token);
        setLoading(false);
        setIsError(false);
      } catch (error) {
        setLoading(false);
        setIsError(true);
        console.log(error);
      }
    }
  };

  const data = use(
    callAPI()
      .then(() => console.log("thnahf công"))
      .catch(() => console.log("lỗi"))
  );

  console.log({ data });

  if (isError) return <div>Lỗi</div>;

  return <div>{loading ? "Đang load ...." : "Đã verify"}</div>;
};
