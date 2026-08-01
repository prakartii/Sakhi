import { createFileRoute } from "@tanstack/react-router";
import { Sparkles } from "lucide-react";
import { ComingSoon } from "@/components/sakhi/ComingSoon";

export const Route = createFileRoute("/advisor")({
  head: () => ({
    meta: [
      { title: "AI Advisor — Sakhi" },
      {
        name: "description",
        content: "Ask Sakhi what to do next — advice grounded in your own business, brand and sales data.",
      },
    ],
  }),
  component: Advisor,
});

function Advisor() {
  return (
    <ComingSoon
      eyebrow="Ask Sakhi"
      title="“What should I"
      accent="do this week?”"
      copy="A running conversation grounded in your business profile, brand, sales and analytics — not generic advice."
      icon={Sparkles}
      tone="lilac"
      capabilities={[
        "Grounded in your business profile",
        "Growth & marketing suggestions",
        "Explains the why behind advice",
        "Remembers past conversations",
      ]}
    />
  );
}
