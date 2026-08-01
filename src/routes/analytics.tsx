import { createFileRoute } from "@tanstack/react-router";
import { LineChart } from "lucide-react";
import { ComingSoon } from "@/components/sakhi/ComingSoon";

export const Route = createFileRoute("/analytics")({
  head: () => ({
    meta: [
      { title: "Analytics — Sakhi" },
      {
        name: "description",
        content: "Followers, reach, engagement and sales — with Sakhi explaining what moved the numbers.",
      },
    ],
  }),
  component: Analytics,
});

function Analytics() {
  return (
    <ComingSoon
      eyebrow="Growth data"
      title="Numbers that"
      accent="explain themselves."
      copy="The backend calculates every metric — Sakhi just explains what changed and what to do about it."
      icon={LineChart}
      tone="indigo"
      capabilities={[
        "Followers, reach & engagement",
        "Website visitors & conversions",
        "Best-performing posts and times",
        "Plain-language explanations, not just charts",
      ]}
    />
  );
}
