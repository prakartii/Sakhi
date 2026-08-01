import { createFileRoute } from "@tanstack/react-router";
import { Share2 } from "lucide-react";
import { ComingSoon } from "@/components/sakhi/ComingSoon";

export const Route = createFileRoute("/social-studio")({
  head: () => ({
    meta: [
      { title: "Social Studio — Sakhi" },
      {
        name: "description",
        content: "Connect Instagram, LinkedIn and Facebook, and see growth across every channel in one place.",
      },
    ],
  }),
  component: SocialStudio,
});

function SocialStudio() {
  return (
    <ComingSoon
      eyebrow="Social accounts"
      title="Every channel,"
      accent="one place."
      copy="Connect Instagram, LinkedIn and Facebook to see posts, growth and engagement without switching apps."
      icon={Share2}
      tone="lilac"
      capabilities={[
        "Connect Instagram, LinkedIn & Facebook",
        "Post status across channels",
        "Follower & engagement growth",
        "One inbox for all channels",
      ]}
    />
  );
}
