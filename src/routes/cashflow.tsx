import { createFileRoute } from "@tanstack/react-router";
import { Page } from "@/components/sakhi/Layout";
import { MicPanel } from "@/components/sakhi/MicPanel";
import { Reveal } from "@/components/sakhi/Reveal";
import {
  Action,
  Basis,
  Craft,
  Eyebrow,
  HandNote,
  Hero,
  Stat,
  Why,
} from "@/components/sakhi/Cards";

export const Route = createFileRoute("/cashflow")({
  head: () => ({
    meta: [
      { title: "Cashflow — your money, explained in sentences" },
      {
        name: "description",
        content:
          "What came in, what went out, and the one thing to fix this month before it costs you. Sakhi explains cashflow in plain sentences.",
      },
      { property: "og:title", content: "Cashflow — your money, explained in sentences" },
      {
        property: "og:description",
        content: "Financial health for micro-entrepreneurs, without spreadsheets.",
      },
    ],
  }),
  component: Cashflow;
});

function Cashflow() {
  return <Page />;
}
