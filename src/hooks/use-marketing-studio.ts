import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { usePrimaryBusinessProfile } from "@/hooks/use-business-profile";
import type { MarketingAnalysis, MarketingAnalysisListResponse } from "@/lib/types";

function historyQueryKey(profileId: string | undefined) {
  return ["marketing-studio-history", profileId];
}

/** Past Marketing Studio analyses and generated reel briefs for the
 * primary business, newest first (GET /marketing-studio). */
export function useMarketingHistory() {
  const { profile, hasProfile, isLoading: profileLoading } = usePrimaryBusinessProfile();
  const query = useQuery({
    queryKey: historyQueryKey(profile?.id),
    queryFn: () =>
      api.get<MarketingAnalysisListResponse>("/marketing-studio", {
        business_profile_id: profile!.id,
        limit: 30,
      }),
    enabled: hasProfile && !!profile,
  });
  return {
    items: query.data?.items ?? [],
    isLoading: profileLoading || query.isLoading,
  };
}

export interface AnalyzeContentInput {
  socialConnectionId?: string | undefined;
  sourceType: "manual" | "screenshot" | "video_frame" | "link";
  sourceUrl?: string | undefined;
  caption?: string | undefined;
  hashtags: string;
  commentsSample: string;
  views?: string | undefined;
  likes?: string | undefined;
  comments?: string | undefined;
  shares?: string | undefined;
  saves?: string | undefined;
  thumbnail?: Blob | undefined;
}

/** Analyzes a piece of already-posted content — caption, hashtags,
 * metrics, comments, and (optionally) a thumbnail image — via
 * POST /marketing-studio/analyze. Never fetches the real post itself: no
 * Instagram API credentials exist in this app (see the endpoint's own
 * docstring) — every field here is exactly what the caller supplies. */
export function useAnalyzeContent() {
  const queryClient = useQueryClient();
  const { profile } = usePrimaryBusinessProfile();
  return useMutation({
    mutationFn: (input: AnalyzeContentInput) => {
      const form = new FormData();
      form.append("business_profile_id", profile!.id);
      if (input.socialConnectionId) form.append("social_connection_id", input.socialConnectionId);
      form.append("source_type", input.sourceType);
      if (input.sourceUrl) form.append("source_url", input.sourceUrl);
      if (input.caption) form.append("caption", input.caption);
      form.append("hashtags", input.hashtags);
      form.append("comments_sample", input.commentsSample);
      if (input.views) form.append("views", input.views);
      if (input.likes) form.append("likes", input.likes);
      if (input.comments) form.append("comments", input.comments);
      if (input.shares) form.append("shares", input.shares);
      if (input.saves) form.append("saves", input.saves);
      if (input.thumbnail) form.append("thumbnail", input.thumbnail, "thumbnail.jpg");
      return api.postForm<MarketingAnalysis>("/marketing-studio/analyze", form);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: historyQueryKey(profile?.id) });
    },
  });
}

/** Generates a shootable brief (hook, script, shot list, caption,
 * hashtags, CTA) for a new reel — not a rendered video, see
 * POST /marketing-studio/generate-reel's docstring. */
export function useGenerateReel() {
  const queryClient = useQueryClient();
  const { profile } = usePrimaryBusinessProfile();
  return useMutation({
    mutationFn: (angle: string | undefined) =>
      api.post<MarketingAnalysis>("/marketing-studio/generate-reel", {
        business_profile_id: profile!.id,
        angle: angle || undefined,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: historyQueryKey(profile?.id) });
    },
  });
}

/** Generates a cover visual for a reel brief with Nano Banana (Gemini 2.5
 * Flash Image) — free tier, additive (POST
 * /marketing-studio/{id}/generate-visual). */
export function useGenerateReelVisual() {
  const queryClient = useQueryClient();
  const { profile } = usePrimaryBusinessProfile();
  return useMutation({
    mutationFn: (analysisId: string) =>
      api.post<MarketingAnalysis>(`/marketing-studio/${analysisId}/generate-visual`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: historyQueryKey(profile?.id) });
    },
  });
}

/** Generates a video for a reel brief with fal.ai — a real, billed API
 * call, no ongoing free tier; additive (POST
 * /marketing-studio/{id}/generate-video). */
export function useGenerateReelVideo() {
  const queryClient = useQueryClient();
  const { profile } = usePrimaryBusinessProfile();
  return useMutation({
    mutationFn: (analysisId: string) =>
      api.post<MarketingAnalysis>(`/marketing-studio/${analysisId}/generate-video`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: historyQueryKey(profile?.id) });
    },
  });
}
