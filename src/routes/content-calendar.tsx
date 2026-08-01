import { createFileRoute } from "@tanstack/react-router";
import { CalendarDays } from "lucide-react";
import { ComingSoon } from "@/components/sakhi/ComingSoon";

export const Route = createFileRoute("/content-calendar")({
  head: () => ({
    meta: [
      { title: "Content Calendar — Sakhi" },
      {
        name: "description",
        content: "A month of posts — captions, hashtags, reels and posting times — planned and ready to schedule.",
      },
    ],
  }),
  component: ContentCalendar,
});

function ContentCalendar() {
  return (
    <ComingSoon
      eyebrow="Content planning"
      title="A month of posts,"
      accent="planned for you."
      copy="Every post comes with a caption, hashtags, a reel script and the best time to post — ready to schedule."
      icon={CalendarDays}
      tone="rose"
      capabilities={[
        "Monthly & weekly calendar",
        "Captions, hashtags & reel scripts",
        "Carousel and story ideas",
        "Auto-scheduling to your channels",
      ]}
    />
  );
}
