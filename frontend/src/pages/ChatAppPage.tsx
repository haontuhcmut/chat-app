import Signout from "@/components/auth/signout";
import { useAuthStore } from "@/stores/useAuthStore";

const ChatAppPage = () => {
  const user = useAuthStore((s) => s.user);

  return (
    <div>
      {user?.username}
      <Signout />
    </div>
  );
};

export default ChatAppPage;
