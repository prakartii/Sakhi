import { useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { toast } from "sonner";
import {
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  ImageIcon,
  IndianRupee,
  Loader2,
  RotateCw,
  Sparkles,
  Trash2,
  Video,
} from "lucide-react";
import { Page } from "@/components/sakhi/Layout";
import { RequireAuth, RequireBusinessProfile } from "@/components/sakhi/RouteGuards";
import { Reveal } from "@/components/sakhi/Reveal";
import { Craft, Eyebrow, Hero, Pill } from "@/components/sakhi/Cards";
import { IconBadge } from "@/components/sakhi/CompanionAssets";
import {
  useDeleteCalendarItem,
  useGenerateCalendar,
  useGenerateItemImage,
  useGenerateItemVideo,
  useMonthlyCalendar,
  useRegenerateCalendarItem,
  useUpdateCalendarItem,
} from "@/hooks/use-content-calendar";
import { ApiError } from "@/lib/api-client";
import type {
  CampaignFocus,
  ContentCalendarItem,
  ContentStatus,
  SocialPlatform,
} from "@/lib/types";

export const Route = createFileRoute("/content-calendar")({
  head: () => ({
    meta: [
      { title: "AI Content Calendar — Sakhi" },
      {
        name: "description",
        content:
          "A month of captions, hashtags and CTAs planned for you — festival-aware, platform-wise, and yours to edit, regenerate or reschedule.",
      },
    ],
  }),
  component: ContentCalendarRoute,
});

function ContentCalendarRoute() {
  return (
    <RequireAuth>
      <RequireBusinessProfile redirectWhen="missing" redirectTo="/business-setup">
        <ContentCalendarPage />
      </RequireBusinessProfile>
    </RequireAuth>
  );
}

const PLATFORMS: { value: SocialPlatform; label: string }[] = [
  { value: "instagram", label: "Instagram" },
  { value: "facebook", label: "Facebook" },
  { value: "linkedin", label: "LinkedIn" },
  { value: "pinterest", label: "Pinterest" },
];

const PLATFORM_TONE: Record<SocialPlatform, "rose" | "indigo" | "leaf" | "marigold"> = {
  instagram: "rose",
  facebook: "indigo",
  linkedin: "leaf",
  pinterest: "marigold",
};

const STATUS_TONE: Record<ContentStatus, "rose" | "indigo" | "leaf" | "marigold"> = {
  draft: "marigold",
  scheduled: "indigo",
  published: "leaf",
  failed: "rose",
  cancelled: "rose",
};

const CAMPAIGN_FOCUS_OPTIONS: { value: CampaignFocus; label: string }[] = [
  { value: "general", label: "General mix" },
  { value: "festival", label: "Festival & seasonal" },
  { value: "product_launch", label: "Product launch" },
  { value: "promotional_offer", label: "Promotional offer" },
  { value: "bundle_idea", label: "Bundle idea" },
];

const WEEKDAY_LABELS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const MONTH_LABEL_FMT = new Intl.DateTimeFormat("en-IN", { month: "long", year: "numeric" });

function itemsByDay(items: ContentCalendarItem[]): Map<string, ContentCalendarItem[]> {
  const map = new Map<string, ContentCalendarItem[]>();
  for (const item of items) {
    if (!item.scheduled_datetime) continue;
    const key = item.scheduled_datetime.slice(0, 10);
    const bucket = map.get(key) ?? [];
    bucket.push(item);
    map.set(key, bucket);
  }
  return map;
}

function buildWeeks(year: number, month: number): (Date | null)[][] {
  const first = new Date(year, month - 1, 1);
  const daysInMonth = new Date(year, month, 0).getDate();
  const startWeekday = first.getDay();

  const cells: (Date | null)[] = Array.from({ length: startWeekday }, () => null);
  for (let day = 1; day <= daysInMonth; day++) cells.push(new Date(year, month - 1, day));
  while (cells.length % 7 !== 0) cells.push(null);

  const weeks: (Date | null)[][] = [];
  for (let i = 0; i < cells.length; i += 7) weeks.push(cells.slice(i, i + 7));
  return weeks;
}

function dateKey(d: Date): string {
  // Deliberately NOT toISOString() — that converts to UTC, which shifts
  // the date backward a day for any timezone ahead of UTC (e.g. IST) since
  // these Date objects are constructed at local midnight, not UTC midnight.
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function GeneratePanel({
  year,
  month,
  onGenerated,
}: {
  year: number;
  month: number;
  onGenerated: () => void;
}) {
  const generate = useGenerateCalendar();
  const [platforms, setPlatforms] = useState<SocialPlatform[]>(["instagram", "facebook"]);
  const [postsPerWeek, setPostsPerWeek] = useState(3);
  const [focus, setFocus] = useState<CampaignFocus>("general");
  const [note, setNote] = useState("");

  function togglePlatform(p: SocialPlatform) {
    setPlatforms((cur) => (cur.includes(p) ? cur.filter((x) => x !== p) : [...cur, p]));
  }

  function handleGenerate() {
    if (platforms.length === 0) {
      toast.error("Pick at least one platform.");
      return;
    }
    generate.mutate(
      {
        month: `${year}-${String(month).padStart(2, "0")}-01`,
        platforms,
        posts_per_week: postsPerWeek,
        campaign_focus: focus,
        ...(focus !== "general" && note.trim() ? { campaign_note: note.trim() } : {}),
      },
      {
        onSuccess: (data) => {
          toast.success(
            `${data.items.length} posts planned for ${MONTH_LABEL_FMT.format(new Date(year, month - 1, 1))}`,
          );
          onGenerated();
        },
        onError: (error) =>
          toast.error(error instanceof ApiError ? error.message : "Couldn't generate a calendar"),
      },
    );
  }

  return (
    <Craft tone="lilac" texture="weave">
      <div className="flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-wine" />
        <Eyebrow>Generate a month</Eyebrow>
      </div>

      <div className="mt-4">
        <p className="mb-1.5 text-[12px] font-medium text-foreground/80">Platforms</p>
        <div className="flex flex-wrap gap-2">
          {PLATFORMS.map((p) => (
            <button
              key={p.value}
              type="button"
              onClick={() => togglePlatform(p.value)}
              className={`rounded-full border px-3 py-1.5 text-[11.5px] font-medium transition-colors ${
                platforms.includes(p.value)
                  ? "border-wine/40 bg-wine text-primary-foreground"
                  : "border-clay/25 bg-card text-foreground/70 hover:border-wine/30"
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <label className="block">
          <span className="mb-1.5 block text-[12px] font-medium text-foreground/80">
            Posts per week
          </span>
          <input
            type="number"
            min={1}
            max={7}
            value={postsPerWeek}
            onChange={(e) => setPostsPerWeek(Number(e.target.value) || 1)}
            className="w-full rounded-xl border border-clay/25 bg-card px-3.5 py-2 text-[13.5px] shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-wine/30"
          />
        </label>
        <label className="block">
          <span className="mb-1.5 block text-[12px] font-medium text-foreground/80">
            Campaign focus
          </span>
          <select
            value={focus}
            onChange={(e) => setFocus(e.target.value as CampaignFocus)}
            className="w-full rounded-xl border border-clay/25 bg-card px-3.5 py-2 text-[13.5px] shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-wine/30"
          >
            {CAMPAIGN_FOCUS_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      {focus !== "general" && (
        <label className="mt-3 block">
          <span className="mb-1.5 block text-[12px] font-medium text-foreground/80">
            {focus === "product_launch"
              ? "Which product, and when's the launch?"
              : focus === "promotional_offer"
                ? "What's the offer?"
                : "What's in the bundle?"}
          </span>
          <input
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="A sentence is enough — Sakhi builds the campaign around it"
            className="w-full rounded-xl border border-clay/25 bg-card px-3.5 py-2 text-[13.5px] shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-wine/30"
          />
        </label>
      )}

      <button
        type="button"
        onClick={handleGenerate}
        disabled={generate.isPending}
        className="mt-4 flex items-center gap-1.5 rounded-xl bg-primary px-4 py-2.5 text-[13px] font-semibold text-primary-foreground transition-transform hover:-translate-y-0.5 disabled:opacity-70"
      >
        {generate.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
        Generate {MONTH_LABEL_FMT.format(new Date(year, month - 1, 1))}
      </button>
      <p className="mt-2 text-[11px] text-muted-foreground">
        Each generated post starts as a draft — nothing publishes anywhere on its own.
      </p>
    </Craft>
  );
}

function ItemDetail({ item, onClose }: { item: ContentCalendarItem; onClose: () => void }) {
  const update = useUpdateCalendarItem();
  const regenerate = useRegenerateCalendarItem();
  const del = useDeleteCalendarItem();
  const generateImage = useGenerateItemImage();
  const generateVideo = useGenerateItemVideo();

  const [caption, setCaption] = useState(item.caption ?? "");
  const [hashtags, setHashtags] = useState((item.hashtags ?? []).join(" "));
  const [cta, setCta] = useState(item.call_to_action ?? "");
  const [scheduledDate, setScheduledDate] = useState(item.scheduled_datetime?.slice(0, 10) ?? "");
  const [scheduledTime, setScheduledTime] = useState(
    item.scheduled_datetime?.slice(11, 16) ?? "18:00",
  );
  const [instructions, setInstructions] = useState("");

  function handleSave() {
    update.mutate(
      {
        id: item.id,
        caption,
        hashtags: hashtags
          .split(/[\s,]+/)
          .map((h) => h.trim())
          .filter(Boolean),
        call_to_action: cta,
        // Sent as a plain local wall-clock string, not through
        // new Date(...).toISOString() — same UTC-shift bug as dateKey()
        // above would otherwise silently move the save to the wrong day.
        scheduled_datetime: scheduledDate ? `${scheduledDate}T${scheduledTime}:00` : null,
      },
      {
        onSuccess: () => toast.success("Saved"),
        onError: (error) =>
          toast.error(error instanceof ApiError ? error.message : "Couldn't save"),
      },
    );
  }

  function handleRegenerate() {
    regenerate.mutate(
      { id: item.id, ...(instructions.trim() ? { instructions: instructions.trim() } : {}) },
      {
        onSuccess: (data) => {
          setCaption(data.caption ?? "");
          setHashtags((data.hashtags ?? []).join(" "));
          setCta(data.call_to_action ?? "");
          toast.success("Regenerated");
        },
        onError: (error) =>
          toast.error(error instanceof ApiError ? error.message : "Couldn't regenerate"),
      },
    );
  }

  function handleDelete() {
    del.mutate(item.id, {
      onSuccess: () => {
        toast.success("Removed from the calendar");
        onClose();
      },
      onError: (error) =>
        toast.error(error instanceof ApiError ? error.message : "Couldn't delete"),
    });
  }

  function handleGenerateImage() {
    generateImage.mutate(item.id, {
      onSuccess: () => toast.success("Image generated"),
      onError: (error) =>
        toast.error(error instanceof ApiError ? error.message : "Couldn't generate an image"),
    });
  }

  function handleGenerateVideo() {
    generateVideo.mutate(item.id, {
      onSuccess: () => toast.success("Video generated"),
      onError: (error) =>
        toast.error(error instanceof ApiError ? error.message : "Couldn't generate a video"),
    });
  }

  return (
    <Craft tone="cream" className="sticky top-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex flex-wrap gap-1.5">
          <Pill tone={PLATFORM_TONE[item.platform]}>{item.platform}</Pill>
          <Pill tone="indigo">{item.content_type}</Pill>
          <Pill tone={STATUS_TONE[item.status]}>{item.status}</Pill>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="text-[11px] text-muted-foreground hover:text-wine"
        >
          Close
        </button>
      </div>

      <label className="mt-4 block">
        <span className="mb-1.5 block text-[12px] font-medium text-foreground/80">Caption</span>
        <textarea
          value={caption}
          onChange={(e) => setCaption(e.target.value)}
          rows={5}
          className="w-full resize-none rounded-xl border border-clay/25 bg-card px-3.5 py-2.5 text-[13px] leading-relaxed shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-wine/30"
        />
      </label>

      <label className="mt-3 block">
        <span className="mb-1.5 block text-[12px] font-medium text-foreground/80">Hashtags</span>
        <input
          value={hashtags}
          onChange={(e) => setHashtags(e.target.value)}
          className="w-full rounded-xl border border-clay/25 bg-card px-3.5 py-2 text-[13px] shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-wine/30"
        />
      </label>

      <label className="mt-3 block">
        <span className="mb-1.5 block text-[12px] font-medium text-foreground/80">
          Call to action
        </span>
        <input
          value={cta}
          onChange={(e) => setCta(e.target.value)}
          className="w-full rounded-xl border border-clay/25 bg-card px-3.5 py-2 text-[13px] shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-wine/30"
        />
      </label>

      <div className="mt-3 grid grid-cols-2 gap-2">
        <label className="block">
          <span className="mb-1.5 block text-[12px] font-medium text-foreground/80">Date</span>
          <input
            type="date"
            value={scheduledDate}
            onChange={(e) => setScheduledDate(e.target.value)}
            className="w-full rounded-xl border border-clay/25 bg-card px-3 py-2 text-[13px] shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-wine/30"
          />
        </label>
        <label className="block">
          <span className="mb-1.5 block text-[12px] font-medium text-foreground/80">Time</span>
          <input
            type="time"
            value={scheduledTime}
            onChange={(e) => setScheduledTime(e.target.value)}
            className="w-full rounded-xl border border-clay/25 bg-card px-3 py-2 text-[13px] shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-wine/30"
          />
        </label>
      </div>

      {item.image_prompt && (
        <p className="mt-3 text-[11px] text-muted-foreground">
          <span className="font-semibold text-foreground/70">Image prompt: </span>
          {item.image_prompt}
        </p>
      )}

      <div className="mt-4 border-t border-clay/15 pt-3">
        <Eyebrow>AI media</Eyebrow>

        {item.generated_image_url && (
          <img
            src={item.generated_image_url}
            alt="AI-generated visual for this post"
            className="mt-2 w-full rounded-xl border border-clay/20 object-cover"
          />
        )}
        {item.generated_video_url && (
          <video
            src={item.generated_video_url}
            controls
            className="mt-2 w-full rounded-xl border border-clay/20"
          />
        )}

        <div className="mt-2 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={handleGenerateImage}
            disabled={generateImage.isPending}
            className="flex items-center gap-1.5 rounded-xl border border-clay/25 px-3.5 py-2 text-[12px] font-medium text-foreground/75 transition-colors hover:border-wine/30 hover:text-wine disabled:opacity-70"
          >
            {generateImage.isPending ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <ImageIcon className="h-3.5 w-3.5" />
            )}
            {item.generated_image_url ? "Regenerate image" : "Generate image"}
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
            {item.generated_video_url ? "Regenerate video" : "Generate video"}
          </button>
        </div>
        <p className="mt-1.5 flex items-start gap-1 text-[10.5px] text-muted-foreground">
          <IndianRupee className="mt-px h-3 w-3 shrink-0" />
          Image generation is free. Video generation costs real money per clip (fal.ai) — generate
          only when you mean it.
        </p>
      </div>

      <div className="mt-4 border-t border-clay/15 pt-3">
        <label className="block">
          <span className="mb-1.5 block text-[12px] font-medium text-foreground/80">
            Regenerate with instructions (optional)
          </span>
          <input
            value={instructions}
            onChange={(e) => setInstructions(e.target.value)}
            placeholder="e.g. make it shorter, lean into the festival more"
            className="w-full rounded-xl border border-clay/25 bg-card px-3.5 py-2 text-[13px] shadow-sm outline-none focus-visible:ring-2 focus-visible:ring-wine/30"
          />
        </label>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={handleSave}
          disabled={update.isPending}
          className="rounded-xl bg-primary px-4 py-2 text-[12.5px] font-semibold text-primary-foreground transition-transform hover:-translate-y-0.5 disabled:opacity-70"
        >
          {update.isPending ? "Saving…" : "Save changes"}
        </button>
        <button
          type="button"
          onClick={handleRegenerate}
          disabled={regenerate.isPending}
          className="flex items-center gap-1.5 rounded-xl border border-clay/25 px-4 py-2 text-[12.5px] font-medium text-foreground/75 transition-colors hover:border-wine/30 hover:text-wine disabled:opacity-70"
        >
          {regenerate.isPending ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <RotateCw className="h-3.5 w-3.5" />
          )}
          Regenerate
        </button>
        <button
          type="button"
          onClick={handleDelete}
          disabled={del.isPending}
          className="flex items-center gap-1.5 rounded-xl border border-rose/40 px-4 py-2 text-[12.5px] font-medium text-wine transition-colors hover:bg-rose/40 disabled:opacity-70"
        >
          <Trash2 className="h-3.5 w-3.5" />
          Delete
        </button>
      </div>
    </Craft>
  );
}

function ContentCalendarPage() {
  const today = new Date();
  const [year, setYear] = useState(today.getFullYear());
  const [month, setMonth] = useState(today.getMonth() + 1);
  const [selectedDay, setSelectedDay] = useState<string | null>(null);
  const [selectedItemId, setSelectedItemId] = useState<string | null>(null);

  const { items, isLoading } = useMonthlyCalendar(year, month);
  const grouped = useMemo(() => itemsByDay(items), [items]);
  const weeks = useMemo(() => buildWeeks(year, month), [year, month]);

  function shiftMonth(delta: number) {
    let m = month + delta;
    let y = year;
    if (m > 12) {
      m = 1;
      y += 1;
    } else if (m < 1) {
      m = 12;
      y -= 1;
    }
    setMonth(m);
    setYear(y);
    setSelectedDay(null);
    setSelectedItemId(null);
  }

  const dayItems = selectedDay ? (grouped.get(selectedDay) ?? []) : [];
  const selectedItem = items.find((i) => i.id === selectedItemId) ?? null;

  return (
    <Page>
      <section className="py-14 lg:py-16">
        <Reveal>
          <Hero
            eyebrow="AI Content Calendar"
            title="A month of content,"
            accent="planned before you ask."
            copy="Festival-aware, platform-wise captions, hashtags and CTAs — built from your business profile and brand, yours to edit, regenerate or reschedule."
          />
        </Reveal>
      </section>

      <div className="thread opacity-50" />

      <section className="grid gap-6 py-10 lg:grid-cols-[1.3fr_0.9fr]">
        <div className="min-w-0 space-y-5">
          <Reveal>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <IconBadge icon={CalendarDays} tone="indigo" />
                <h2 className="font-display text-xl font-semibold text-foreground">
                  {MONTH_LABEL_FMT.format(new Date(year, month - 1, 1))}
                </h2>
              </div>
              <div className="flex gap-1.5">
                <button
                  type="button"
                  onClick={() => shiftMonth(-1)}
                  className="grid h-8 w-8 place-items-center rounded-full border border-clay/25 text-foreground/70 hover:border-wine/30 hover:text-wine"
                  aria-label="Previous month"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  onClick={() => shiftMonth(1)}
                  className="grid h-8 w-8 place-items-center rounded-full border border-clay/25 text-foreground/70 hover:border-wine/30 hover:text-wine"
                  aria-label="Next month"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          </Reveal>

          <Reveal delay={40}>
            <div className="card-soft overflow-hidden rounded-3xl">
              <div className="grid grid-cols-7 border-b border-clay/15 bg-sand/50">
                {WEEKDAY_LABELS.map((d) => (
                  <div
                    key={d}
                    className="px-2 py-2 text-center text-[10.5px] font-semibold tracking-[0.1em] text-muted-foreground uppercase"
                  >
                    {d}
                  </div>
                ))}
              </div>
              {isLoading ? (
                <div className="flex justify-center py-14">
                  <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                </div>
              ) : (
                weeks.map((week, wi) => (
                  <div key={wi} className="grid grid-cols-7 border-b border-clay/10 last:border-0">
                    {week.map((d, di) => {
                      if (!d) return <div key={di} className="min-h-24 bg-card/30" />;
                      const key = dateKey(d);
                      const dayPosts = grouped.get(key) ?? [];
                      const isSelected = selectedDay === key;
                      return (
                        <button
                          key={di}
                          type="button"
                          onClick={() => {
                            setSelectedDay(key);
                            setSelectedItemId(null);
                          }}
                          className={`min-h-24 border-r border-clay/10 p-1.5 text-left align-top transition-colors last:border-r-0 hover:bg-sand/40 ${
                            isSelected ? "bg-sand/60" : "bg-card"
                          }`}
                        >
                          <span className="text-[11px] font-medium text-foreground/60">
                            {d.getDate()}
                          </span>
                          <div className="mt-1 flex flex-wrap gap-1">
                            {dayPosts.slice(0, 3).map((p) => (
                              <span
                                key={p.id}
                                className={`inline-block h-1.5 w-1.5 rounded-full ${
                                  PLATFORM_TONE[p.platform] === "rose"
                                    ? "bg-wine"
                                    : PLATFORM_TONE[p.platform] === "indigo"
                                      ? "bg-[oklch(0.55_0.09_255)]"
                                      : PLATFORM_TONE[p.platform] === "leaf"
                                        ? "bg-leaf-ink"
                                        : "bg-[oklch(0.55_0.12_70)]"
                                }`}
                              />
                            ))}
                            {dayPosts.length > 3 && (
                              <span className="text-[9px] text-muted-foreground">
                                +{dayPosts.length - 3}
                              </span>
                            )}
                          </div>
                        </button>
                      );
                    })}
                  </div>
                ))
              )}
            </div>
          </Reveal>

          {selectedDay && (
            <Reveal delay={60}>
              <Craft tone="sand">
                <Eyebrow>
                  {new Date(selectedDay).toLocaleDateString("en-IN", {
                    weekday: "long",
                    day: "numeric",
                    month: "long",
                  })}
                </Eyebrow>
                {dayItems.length === 0 ? (
                  <p className="mt-2 text-[12.5px] text-muted-foreground">
                    Nothing planned for this day yet.
                  </p>
                ) : (
                  <div className="mt-3 space-y-2">
                    {dayItems.map((item) => (
                      <button
                        key={item.id}
                        type="button"
                        onClick={() => setSelectedItemId(item.id)}
                        className={`block w-full rounded-xl border px-3.5 py-2.5 text-left transition-colors ${
                          selectedItemId === item.id
                            ? "border-wine/40 bg-card"
                            : "border-clay/20 bg-card/60 hover:border-wine/25"
                        }`}
                      >
                        <div className="flex flex-wrap items-center gap-1.5">
                          <Pill tone={PLATFORM_TONE[item.platform]}>{item.platform}</Pill>
                          <Pill tone="indigo">{item.content_type}</Pill>
                        </div>
                        <p className="mt-1.5 line-clamp-2 text-[12.5px] text-foreground/75">
                          {item.caption || "No caption yet"}
                        </p>
                      </button>
                    ))}
                  </div>
                )}
              </Craft>
            </Reveal>
          )}
        </div>

        <div className="space-y-5">
          <Reveal delay={20}>
            <GeneratePanel year={year} month={month} onGenerated={() => setSelectedDay(null)} />
          </Reveal>
          {selectedItem && (
            <Reveal delay={40}>
              <ItemDetail item={selectedItem} onClose={() => setSelectedItemId(null)} />
            </Reveal>
          )}
        </div>
      </section>
    </Page>
  );
}
