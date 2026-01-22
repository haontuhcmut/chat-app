import ChatWindowLayOut from "@/components/chat/ChatWindowLayOut";
import { AppSidebar } from "@/components/sidebar/app-sidebar";
import { SidebarProvider } from "@/components/ui/sidebar";

const ChatAppPage = () => {
  return (
    <SidebarProvider>
      <AppSidebar />
      <div className="flex h-sceen w-full p-2">
        <ChatWindowLayOut />
      </div>
    </SidebarProvider>
  );
};

export default ChatAppPage;
