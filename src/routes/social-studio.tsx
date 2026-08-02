import { useRef, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { toast } from "sonner";
import {
  Clapperboard,
  Film,
  Gauge,
  Image as ImageIcon,
  IndianRupee,
  Link2,
  Loader2,
  Plug,
  Sparkles,
  Upload,
  Video,
} from "lucide-react";
import { Page } from "@/components/sakhi/Layout";
import { RequireAuth, RequireBusinessProfile } from "@/components/sakhi/RouteGuards";
import { Reveal } from "@/components/sakhi/Reveal";
import { Basis, Craft, Eyebrow, Hero, Meter, Pill, Why } from "@/components/sakhi/Cards";
import { IconBadge } from "@/components/sakhi/CompanionAssets";
import {
  useAnalyzeContent,
  useGenerateReel,
  useGenerateReelVideo,
  useGenerateReelVisual,
  useMarketingHistory,
} from "@/hooks/use-marketing-studio";
import {
  useConnectAccount,
  useDisconnectAccount,
  useSocialConnections,
} from "@/hooks/use-social-connections";
import { ApiError } from "@/lib/api-client";
import type { MarketingAnalysis, MarketingAnalysisSourceType, SocialPlatform } from "@/lib/types";

export const Route = createFileRoute("/social-studio")({
  head: () => ({
    meta: [
      { title: "AI Marketing Studio — Sakhi" },
      {
        name: "description",
        content:
          "Upload a reel or paste its numbers and Sakhi explains why it performed the way it did — then plans your next one.",
      },
    ],
  }),
  component: SocialStudioRoute,
});

function SocialStudioRoute() {
  return (
    <RequireAuth>
      <RequireBusinessProfile redirectWhen="missing" redirectTo="/business-setup">
        <SocialStudio />
      </RequireBusinessProfile>
    </RequireAuth>
  );
}

type Tab = "analyze" | "generate" | "connections";

const TABS: { id: Tab; label: string; icon: typeof Film }[] = [
  { id: "analyze", label: "Analyze content", icon: Film },
  { id: "generate", label: "Generate a reel", icon: Clapperboard },
  { id: "connections", label: "Connections", icon: Plug },
];

const SOURCE_TYPES: { value: MarketingAnalysisSourceType; label: string }[] = [
  { value: "manual", label: "Manual metrics" },
  { value: "screenshot", label: "Analytics screenshot" },
  { value: "video_frame", label: "Reel upload" },
  { value: "link", label: "Link (reference only)" },
];

/** Grabs one frame from an uploaded video file as a JPEG blob, entirely in
 * the browser — this app has no video-understanding AI, so "upload a
 * reel" means "upload the file, and Sakhi looks at a representative frame
 * plus whatever caption/metrics/comments you give her," not that she
 * watches the video. */
function extractVideoFrame(file: File): Promise<Blob> {
  return new Promise((resolve, reject) => {
    const video = document.createElement("video");
    video.preload = "metadata";
    video.muted = true;
    video.src = URL.createObjectURL(file);
    video.onloadeddata = () => {
      video.currentTime = Math.min(1, video.duration / 2);
    };
    video.onseeked = () => {
      const canvas = document.createElement("canvas");
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext("2d");
      if (!ctx) {
        reject(new Error("Canvas not supported"));
        return;
      }
      ctx.drawImage(video, 0, 0);
      canvas.toBlob(
        (blob) => {
          URL.revokeObjectURL(video.src);
          if (blob) resolve(blob);
          else reject(new Error("Couldn't extract a frame"));
        },
        "image/jpeg",
        0.85,
      );
    };
    video.onerror = () => reject(new Error("Couldn't read that video file"));
  });
}

function ScorePill({ score }: { score: number }) {
  const tone = score >= 70 ? "leaf" : score >= 40 ? "marigold" : "rose";
  return (
    <div className="flex items-center gap-3">
      <span
        className={`font-display text-3xl font-semibold ${tone === "leaf" ? "text-leaf-ink" : tone === "marigold" ? "text-[oklch(0.42_0.09_70)]" : "text-wine"}`}
      >
        {Math.round(score)}
      </span>
      <div className="flex-1">
        <Eyebrow>Virality score</Eyebrow>
        <Meter value={score} tone={tone === "rose" ? "wine" : "clay"} />
      </div>
    </div>
  );
}

function RatedCard({
  label,
  feedback,
}: {
  label: string;
  feedback: import("@/lib/types").RatedFeedback | null;
}) {
  if (!feedback) return null;
  const tone = feedback.rating.toLowerCase().includes("strong")
    ? "leaf"
    : feedback.rating.toLowerCase().includes("weak")
      ? "rose"
      : "marigold";
  return (
    <div className="rounded-2xl bg-card/70 px-4 py-3">
      <div className="flex items-center justify-between gap-2">
        <p className="text-[12.5px] font-semibold text-foreground">{label}</p>
        <Pill tone={tone}>{feedback.rating}</Pill>
      </div>
      <p className="mt-1.5 text-[12.5px] text-foreground/70">{feedback.feedback}</p>
    </div>
  );
}

function AnalysisResults({ item }: { item: MarketingAnalysis }) {
  const a = item.analysis;
  if (!a) return null;
  return (
    <div className="space-y-5">
      <Craft tone="marigold" texture="weave">
        <ScorePill score={a.virality_score} />
        <Why>{a.virality_reasoning}</Why>
        <Basis>
          {item.engagement_rate !== null
            ? `Engagement rate: ${item.engagement_rate}% of viewers liked, commented, shared or saved.`
            : "Engagement rate needs a view count to compute."}
        </Basis>
      </Craft>

      <Craft tone="cream">
        <Eyebrow>What's working, what's not</Eyebrow>
        <div className="mt-3 space-y-2.5">
          <RatedCard label="Hook" feedback={a.hook_analysis} />
          <RatedCard label="Caption" feedback={a.caption_analysis} />
          <RatedCard label="Call to action" feedback={a.cta_analysis} />
          <RatedCard label="Thumbnail" feedback={a.thumbnail_analysis} />
        </div>
      </Craft>

      <div className="grid gap-5 sm:grid-cols-2">
        <Craft tone="indigo" texture="blockprint">
          <Eyebrow>Audience sentiment</Eyebrow>
          <div className="mt-3 flex gap-1.5">
            <Pill tone="leaf">{Math.round(a.audience_sentiment.positive_pct)}% positive</Pill>
            <Pill tone="marigold">{Math.round(a.audience_sentiment.neutral_pct)}% neutral</Pill>
            <Pill tone="rose">{Math.round(a.audience_sentiment.negative_pct)}% negative</Pill>
          </div>
          <p className="mt-2.5 text-[12.5px] text-foreground/75">{a.audience_sentiment.summary}</p>
          {a.comment_themes.length > 0 && (
            <>
              <p className="mt-3 text-[11.5px] font-semibold text-foreground/70">Comment themes</p>
              <div className="mt-1.5 flex flex-wrap gap-1.5">
                {a.comment_themes.map((theme) => (
                  <Pill key={theme} tone="indigo">
                    {theme}
                  </Pill>
                ))}
              </div>
            </>
          )}
        </Craft>

        <Craft tone="leaf" texture="weave">
          <Eyebrow>Products detected</Eyebrow>
          {a.product_detection.length === 0 ? (
            <p className="mt-2 text-[12.5px] text-muted-foreground">None detected.</p>
          ) : (
            <div className="mt-2.5 flex flex-wrap gap-1.5">
              {a.product_detection.map((p) => (
                <Pill key={p} tone="leaf">
                  {p}
                </Pill>
              ))}
            </div>
          )}
        </Craft>
      </div>

      <Craft tone="sand">
        <Eyebrow>Recommendations</Eyebrow>
        <ul className="mt-3 space-y-2">
          {a.recommendations.map((r) => (
            <li key={r} className="flex items-start gap-2 text-[12.5px] text-foreground/80">
              <span aria-hidden className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-wine/60" />
              {r}
            </li>
          ))}
        </ul>
      </Craft>

      <div className="grid gap-5 sm:grid-cols-2">
        <Craft tone="lilac" texture="weave">
          <Eyebrow>AI-generated captions</Eyebrow>
          <div className="mt-2.5 space-y-2">
            {a.ai_captions.map((c, i) => (
              <p key={i} className="rounded-xl bg-card/70 px-3 py-2 text-[12px] text-foreground/80">
                {c}
              </p>
            ))}
          </div>
        </Craft>
        <Craft tone="rose" texture="blockprint">
          <Eyebrow>Next reel ideas</Eyebrow>
          <ul className="mt-2.5 space-y-2">
            {a.next_reel_ideas.map((idea) => (
              <li key={idea} className="text-[12.5px] text-foreground/80">
                ✎ {idea}
              </li>
            ))}
          </ul>
        </Craft>
      </div>

      <p className="hand text-[13px]">{a.performance_summary}</p>
    </div>
  );
}

function AnalyzeTab() {
  const analyze = useAnalyzeContent();
  const { items: history } = useMarketingHistory();
  const [sourceType, setSourceType] = useState<MarketingAnalysisSourceType>("manual");
  const [sourceUrl, setSourceUrl] = useState("");
  const [caption, setCaption] = useState("");
  const [hashtags, setHashtags] = useState("");
  const [comments, setComments] = useState("");
  const [views, setViews] = useState("");
  const [likes, setLikes] = useState("");
  const [commentsCount, setCommentsCount] = useState("");
  const [shares, setShares] = useState("");
  const [saves, setSaves] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<MarketingAnalysis | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function handleSubmit() {
    let thumbnail: Blob | undefined;
    try {
      if (file) {
        thumbnail = file.type.startsWith("video/") ? await extractVideoFrame(file) : file;
      }
    } catch {
      toast.error("Couldn't process that file — try a different one.");
      return;
    }

    analyze.mutate(
      {
        sourceType,
        sourceUrl: sourceUrl.trim() || undefined,
        caption: caption.trim() || undefined,
        hashtags,
        commentsSample: comments,
        views: views || undefined,
        likes: likes || undefined,
        comments: commentsCount || undefined,
        shares: shares || undefined,
        saves: saves || undefined,
        thumbnail,
      },
      {
        onSuccess: (data) => {
          setResult(data);
          toast.success("Analysis ready");
        },
        onError: (error) =>
          toast.error(error instanceof ApiError ? error.message : "Couldn't analyze that content"),
      },
    );
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
      <div className="space-y-4">
        <Craft tone="cream">
          <Eyebrow>What are you analyzing?</Eyebrow>
          <div className="mt-3 flex flex-wrap gap-2">
            {SOURCE_TYPES.map((s) => (
              <button
                key={s.value}
                type="button"
                onClick={() => setSourceType(s.value)}
                className={`rounded-full border px-3 py-1.5 text-[11.5px] font-medium transition-colors ${
                  sourceType === s.value
                    ? "border-wine/40 bg-wine text-primary-foreground"
                    : "border-clay/25 bg-card text-foreground/70 hover:border-wine/30"
                }`}
              >
                {s.label}
              </button>
            ))}
          </div>

          {sourceType === "link" && (
            <label className="mt-4 block">
              <span className="mb-1.5 block text-[12px] font-medium text-foreground/80">
                Post link (kept for reference — not fetched automatically)
              </span>
              <div className="flex items-center gap-2 rounded-xl border border-clay/25 bg-card px-3.5 py-2">
                <Link2 className="h-3.5 w-3.5 text-muted-foreground" />
                <input
                  value={sourceUrl}
                  onChange={(e) => setSourceUrl(e.target.value)}
                  placeholder="https://instagram.com/reel/..."
                  className="w-full bg-transparent text-[13px] outline-none"
                />
              </div>
            </label>
          )}

          {(sourceType === "screenshot" || sourceType === "video_frame") && (
            <label className="mt-4 block">
              <span className="mb-1.5 block text-[12px] font-medium text-foreground/80">
                {sourceType === "video_frame" ? "Upload the reel" : "Upload the screenshot"}
              </span>
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="flex w-full items-center justify-center gap-2 rounded-xl border-2 border-dashed border-clay/30 bg-card px-4 py-6 text-[12.5px] text-foreground/70 transition-colors hover:border-wine/30"
              >
                {file ? (
                  <>
                    <ImageIcon className="h-4 w-4" /> {file.name}
                  </>
                ) : (
                  <>
                    <Upload className="h-4 w-4" />
                    {sourceType === "video_frame" ? "Choose a video file" : "Choose an image"}
                  </>
                )}
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept={sourceType === "video_frame" ? "video/*" : "image/*"}
                className="hidden"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              />
              {sourceType === "video_frame" && (
                <p className="mt-1.5 text-[11px] text-muted-foreground">
                  Sakhi looks at one representative frame plus whatever caption/metrics/comments you
                  add below — she doesn't watch the full video.
                </p>
              )}
            </label>
          )}
        </Craft>

        <Craft tone="sand">
          <Eyebrow>Caption &amp; hashtags</Eyebrow>
          <textarea
            value={caption}
            onChange={(e) => setCaption(e.target.value)}
            placeholder="Paste the caption as posted…"
            rows={3}
            className="mt-3 w-full resize-none rounded-xl border border-clay/25 bg-card px-3.5 py-2.5 text-[13px] leading-relaxed shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-wine/30"
          />
          <input
            value={hashtags}
            onChange={(e) => setHashtags(e.target.value)}
            placeholder="Hashtags, comma-separated"
            className="mt-2.5 w-full rounded-xl border border-clay/25 bg-card px-3.5 py-2 text-[13px] shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-wine/30"
          />
        </Craft>

        <Craft tone="indigo" texture="blockprint">
          <Eyebrow>Engagement metrics</Eyebrow>
          <div className="mt-3 grid grid-cols-3 gap-2">
            {[
              ["Views", views, setViews],
              ["Likes", likes, setLikes],
              ["Comments", commentsCount, setCommentsCount],
              ["Shares", shares, setShares],
              ["Saves", saves, setSaves],
            ].map(([label, value, setter]) => (
              <label key={label as string} className="block">
                <span className="mb-1 block text-[10.5px] text-muted-foreground">
                  {label as string}
                </span>
                <input
                  type="number"
                  min={0}
                  value={value as string}
                  onChange={(e) => (setter as (v: string) => void)(e.target.value)}
                  className="w-full rounded-lg border border-clay/25 bg-card px-2.5 py-1.5 text-[12.5px] outline-none focus-visible:ring-2 focus-visible:ring-wine/30"
                />
              </label>
            ))}
          </div>
          <textarea
            value={comments}
            onChange={(e) => setComments(e.target.value)}
            placeholder="Paste a few real comments, one per line…"
            rows={3}
            className="mt-3 w-full resize-none rounded-xl border border-clay/25 bg-card px-3.5 py-2.5 text-[13px] leading-relaxed shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-wine/30"
          />
        </Craft>

        <button
          type="button"
          onClick={handleSubmit}
          disabled={analyze.isPending}
          className="flex items-center gap-1.5 rounded-xl bg-primary px-5 py-2.5 text-[13px] font-semibold text-primary-foreground transition-transform hover:-translate-y-0.5 disabled:opacity-70"
        >
          {analyze.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
          Analyze this content
        </button>

        {history.length > 0 && (
          <Craft tone="cream" className="mt-2">
            <Eyebrow>Recent history</Eyebrow>
            <div className="mt-2.5 space-y-1.5">
              {history
                .filter((h) => h.analysis)
                .slice(0, 6)
                .map((h) => (
                  <button
                    key={h.id}
                    type="button"
                    onClick={() => setResult(h)}
                    className="flex w-full items-center justify-between rounded-lg px-2.5 py-1.5 text-left text-[12px] text-foreground/70 hover:bg-sand/50"
                  >
                    <span className="truncate">{h.caption || "Untitled content"}</span>
                    <span className="shrink-0 font-semibold text-wine">
                      {h.analysis && Math.round(h.analysis.virality_score)}
                    </span>
                  </button>
                ))}
            </div>
          </Craft>
        )}
      </div>

      <div>
        {analyze.isPending ? (
          <div className="flex justify-center py-14">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : result?.analysis ? (
          <AnalysisResults item={result} />
        ) : (
          <Craft tone="sand" className="py-10 text-center">
            <Eyebrow>Nothing analyzed yet</Eyebrow>
            <p className="mt-2 text-[13px] text-foreground/75">
              Fill in what you have on the left — even just the caption and metrics is enough to
              start.
            </p>
          </Craft>
        )}
      </div>
    </div>
  );
}

function GenerateTab() {
  const generate = useGenerateReel();
  const generateVisual = useGenerateReelVisual();
  const generateVideo = useGenerateReelVideo();
  const [angle, setAngle] = useState("");
  const [brief, setBrief] = useState<MarketingAnalysis | null>(null);

  function handleGenerate() {
    generate.mutate(angle.trim() || undefined, {
      onSuccess: (data) => {
        setBrief(data);
        toast.success("Reel brief ready");
      },
      onError: (error) =>
        toast.error(error instanceof ApiError ? error.message : "Couldn't generate a brief"),
    });
  }

  function handleGenerateVisual() {
    if (!brief) return;
    generateVisual.mutate(brief.id, {
      onSuccess: (data) => {
        setBrief(data);
        toast.success("Visual generated");
      },
      onError: (error) =>
        toast.error(error instanceof ApiError ? error.message : "Couldn't generate a visual"),
    });
  }

  function handleGenerateVideo() {
    if (!brief) return;
    generateVideo.mutate(brief.id, {
      onSuccess: (data) => {
        setBrief(data);
        toast.success("Video generated");
      },
      onError: (error) =>
        toast.error(error instanceof ApiError ? error.message : "Couldn't generate a video"),
    });
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
      <Craft tone="lilac" texture="weave">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-wine" />
          <Eyebrow>Plan your next reel</Eyebrow>
        </div>
        <p className="mt-2 text-[12.5px] text-foreground/75">
          Sakhi writes a full shootable brief — hook, script, shot list, caption and hashtags —
          grounded in your products and what's worked before. From there you can also generate an
          actual cover image (Nano Banana) or video (fal.ai) for it, right below.
        </p>
        <label className="mt-4 block">
          <span className="mb-1.5 block text-[12px] font-medium text-foreground/80">
            Any angle in mind? (optional)
          </span>
          <input
            value={angle}
            onChange={(e) => setAngle(e.target.value)}
            placeholder="e.g. something for Diwali, show the packaging process"
            className="w-full rounded-xl border border-clay/25 bg-card px-3.5 py-2 text-[13px] shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-wine/30"
          />
        </label>
        <button
          type="button"
          onClick={handleGenerate}
          disabled={generate.isPending}
          className="mt-4 flex items-center gap-1.5 rounded-xl bg-primary px-5 py-2.5 text-[13px] font-semibold text-primary-foreground transition-transform hover:-translate-y-0.5 disabled:opacity-70"
        >
          {generate.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
          Generate a reel brief
        </button>
      </Craft>

      <div>
        {generate.isPending ? (
          <div className="flex justify-center py-14">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : brief?.reel_brief ? (
          <div className="space-y-4">
            <Craft tone="marigold" texture="weave">
              <Eyebrow>{brief.reel_brief.concept}</Eyebrow>
              <p className="mt-2 font-display text-lg font-semibold text-foreground">
                &ldquo;{brief.reel_brief.hook}&rdquo;
              </p>
            </Craft>
            <div className="grid gap-4 sm:grid-cols-2">
              <Craft tone="cream">
                <Eyebrow>Script</Eyebrow>
                <ol className="mt-2.5 space-y-2">
                  {brief.reel_brief.script_beats.map((beat, i) => (
                    <li key={i} className="text-[12.5px] text-foreground/80">
                      <span className="font-semibold text-wine">{i + 1}.</span> {beat}
                    </li>
                  ))}
                </ol>
              </Craft>
              <Craft tone="indigo" texture="blockprint">
                <Eyebrow>Shot list</Eyebrow>
                <ol className="mt-2.5 space-y-2">
                  {brief.reel_brief.shot_list.map((shot, i) => (
                    <li key={i} className="text-[12.5px] text-foreground/80">
                      <span className="font-semibold text-wine">{i + 1}.</span> {shot}
                    </li>
                  ))}
                </ol>
              </Craft>
            </div>
            <Craft tone="rose" texture="weave">
              <Eyebrow>Caption</Eyebrow>
              <p className="mt-2 text-[13px] text-foreground/80">{brief.reel_brief.caption}</p>
              <div className="mt-3 flex flex-wrap gap-1.5">
                {brief.reel_brief.hashtags.map((h) => (
                  <Pill key={h} tone="rose">
                    #{h}
                  </Pill>
                ))}
              </div>
              <div className="mt-3">
                <Pill tone="marigold">{brief.reel_brief.cta}</Pill>
              </div>
            </Craft>

            <Craft tone="lilac" texture="weave">
              <Eyebrow>AI media for this reel</Eyebrow>
              <p className="mt-1.5 text-[12px] text-foreground/70">
                Grounded in this business's own brand kit and products, same as the brief above.
              </p>

              {brief.reel_brief.image_url && (
                <img
                  src={brief.reel_brief.image_url}
                  alt="AI-generated cover visual for this reel"
                  className="mt-3 w-full rounded-xl border border-clay/20 object-cover"
                />
              )}
              {brief.reel_brief.video_url && (
                <video
                  src={brief.reel_brief.video_url}
                  controls
                  className="mt-3 w-full rounded-xl border border-clay/20"
                />
              )}

              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={handleGenerateVisual}
                  disabled={generateVisual.isPending}
                  className="flex items-center gap-1.5 rounded-xl border border-clay/25 px-3.5 py-2 text-[12px] font-medium text-foreground/75 transition-colors hover:border-wine/30 hover:text-wine disabled:opacity-70"
                >
                  {generateVisual.isPending ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <ImageIcon className="h-3.5 w-3.5" />
                  )}
                  {brief.reel_brief.image_url ? "Regenerate image" : "Generate image"}
                </button>
                <button
                  type="button"
                  onClick={handleGenerateVideo}
                  disabled={generateVideo.isPending}
                  className="flex items-center gap-1.5 rounded-xl border border-clay/25 px-3.5 py-2 text-[12px] font-medium text-foreground/75 transition-colors hover:border-wine/30 hover:text-wine disabled:opacity-70"
                >
                  {generateVideo.isPending ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Video className="h-3.5 w-3.5" />
                  )}
                  {brief.reel_brief.video_url ? "Regenerate video" : "Generate video"}
                </button>
              </div>
              <p className="mt-1.5 flex items-start gap-1 text-[10.5px] text-muted-foreground">
                <IndianRupee className="mt-px h-3 w-3 shrink-0" />
                Image generation is free. Video generation costs real money per clip (fal.ai) —
                generate only when you mean it.
              </p>
            </Craft>
          </div>
        ) : (
          <Craft tone="sand" className="py-10 text-center">
            <Eyebrow>No brief yet</Eyebrow>
            <p className="mt-2 text-[13px] text-foreground/75">
              Hit generate — Sakhi will plan a full reel from your business profile and brand.
            </p>
          </Craft>
        )}
      </div>
    </div>
  );
}

const PLATFORM_OPTIONS: SocialPlatform[] = ["instagram", "facebook", "linkedin", "pinterest"];

function ConnectionsTab() {
  const { items: connections, isLoading } = useSocialConnections();
  const connect = useConnectAccount();
  const disconnect = useDisconnectAccount();
  const [platform, setPlatform] = useState<SocialPlatform>("instagram");
  const [accountName, setAccountName] = useState("");
  const [accessToken, setAccessToken] = useState("");

  function handleConnect() {
    if (!accessToken.trim()) {
      toast.error("Paste an access token to connect.");
      return;
    }
    connect.mutate(
      { platform, account_name: accountName.trim() || undefined, access_token: accessToken.trim() },
      {
        onSuccess: () => {
          toast.success(`${platform} connected`);
          setAccountName("");
          setAccessToken("");
        },
        onError: (error) =>
          toast.error(error instanceof ApiError ? error.message : "Couldn't connect that account"),
      },
    );
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
      <Craft tone="indigo" texture="blockprint">
        <div className="flex items-center gap-2">
          <Plug className="h-4 w-4 text-wine" />
          <Eyebrow>Connect an account</Eyebrow>
        </div>
        <p className="mt-2 text-[12px] text-foreground/70">
          This app has no live &ldquo;Sign in with Instagram&rdquo; button — that needs a Meta
          Developer app plus Instagram Graph API access, which only gets approved after Meta's own
          App Review of a real, published business. If you already have an access token from your
          own Meta app, paste it here to record the connection.
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          {PLATFORM_OPTIONS.map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => setPlatform(p)}
              className={`rounded-full border px-3 py-1.5 text-[11.5px] font-medium capitalize transition-colors ${
                platform === p
                  ? "border-wine/40 bg-wine text-primary-foreground"
                  : "border-clay/25 bg-card text-foreground/70 hover:border-wine/30"
              }`}
            >
              {p}
            </button>
          ))}
        </div>
        <input
          value={accountName}
          onChange={(e) => setAccountName(e.target.value)}
          placeholder="Account name (optional)"
          className="mt-3 w-full rounded-xl border border-clay/25 bg-card px-3.5 py-2 text-[13px] shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-wine/30"
        />
        <input
          value={accessToken}
          onChange={(e) => setAccessToken(e.target.value)}
          placeholder="Access token"
          type="password"
          className="mt-2.5 w-full rounded-xl border border-clay/25 bg-card px-3.5 py-2 text-[13px] shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-wine/30"
        />
        <button
          type="button"
          onClick={handleConnect}
          disabled={connect.isPending}
          className="mt-4 flex items-center gap-1.5 rounded-xl bg-primary px-4 py-2.5 text-[13px] font-semibold text-primary-foreground transition-transform hover:-translate-y-0.5 disabled:opacity-70"
        >
          {connect.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
          Connect
        </button>
      </Craft>

      <Craft tone="cream">
        <Eyebrow>Connected accounts</Eyebrow>
        {isLoading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          </div>
        ) : connections.length === 0 ? (
          <p className="mt-3 text-[12.5px] text-muted-foreground">Nothing connected yet.</p>
        ) : (
          <div className="mt-3 space-y-2.5">
            {connections.map((c) => (
              <div
                key={c.id}
                className="flex items-center justify-between gap-3 rounded-xl border border-clay/20 bg-card/70 px-4 py-3"
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-foreground capitalize">{c.platform}</span>
                    <Pill tone={c.connection_status === "connected" ? "leaf" : "rose"}>
                      {c.connection_status}
                    </Pill>
                  </div>
                  {c.account_name && (
                    <p className="mt-0.5 truncate text-[11.5px] text-muted-foreground">
                      {c.account_name}
                    </p>
                  )}
                </div>
                {c.connection_status === "connected" && (
                  <button
                    type="button"
                    onClick={() => disconnect.mutate(c.id)}
                    className="shrink-0 text-[11.5px] text-muted-foreground hover:text-wine"
                  >
                    Disconnect
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
        <p className="mt-4 text-[11px] text-muted-foreground">
          Publishing a reel directly to Instagram from Sakhi also requires that same Meta App Review
          approval — the connection above is what a real publish flow would use once that's in
          place, but no publish action is wired up yet.
        </p>
      </Craft>
    </div>
  );
}

function SocialStudio() {
  const [tab, setTab] = useState<Tab>("analyze");

  return (
    <Page>
      <section className="py-14 lg:py-16">
        <Reveal>
          <Hero
            eyebrow="AI Marketing Studio"
            title="Know why it worked,"
            accent="then do it again."
            copy="Upload a reel, paste its numbers, or drop a few comments — Sakhi explains what drove the result and plans what to post next."
          />
        </Reveal>
      </section>

      <div className="thread opacity-50" />

      <section className="flex gap-2 py-6">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-1.5 rounded-full px-4 py-2 text-[13px] font-medium transition-colors ${
              tab === t.id
                ? "bg-primary text-primary-foreground"
                : "border border-clay/25 bg-card text-foreground/70 hover:border-wine/30"
            }`}
          >
            <t.icon className="h-3.5 w-3.5" />
            {t.label}
          </button>
        ))}
      </section>

      <section className="pb-10">
        {tab === "analyze" && <AnalyzeTab />}
        {tab === "generate" && <GenerateTab />}
        {tab === "connections" && <ConnectionsTab />}
      </section>
    </Page>
  );
}
