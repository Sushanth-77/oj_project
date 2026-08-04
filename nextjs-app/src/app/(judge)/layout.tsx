import { Header } from "@/components/layout/Header";
import { AnnouncementBanner } from "@/components/layout/AnnouncementBanner";

export default function JudgeLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <Header />
      <AnnouncementBanner />
      <main className="flex-1">
        {children}
      </main>
    </>
  );
}
