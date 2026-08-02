import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { usePrimaryBusinessProfile } from "@/hooks/use-business-profile";
import type {
  CampaignFocus,
  ContentCalendarGenerateResponse,
  ContentCalendarItem,
  ContentCalendarItemListResponse,
} from "@/lib/types";

function monthlyQueryKey(profileId: string | undefined, year: number, month: number) {
  return ["content-calendar-monthly", profileId, year, month];
}

/** One calendar month's planned content (GET /content-calendar/monthly). */
export function useMonthlyCalendar(year: number, month: number) {
  const { profile, hasProfile, isLoading: profileLoading } = usePrimaryBusinessProfile();
  const query = useQuery({
    queryKey: monthlyQueryKey(profile?.id, year, month),
    queryFn: () =>
      api.get<ContentCalendarItemListResponse>("/content-calendar/monthly", {
        business_profile_id: profile!.id,
        year,
        month,
      }),
    enabled: hasProfile && !!profile,
  });
  return {
    items: query.data?.items ?? [],
    isLoading: profileLoading || query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
  };
}

/** Generates a full month of AI content — rule-based scheduling + one LLM
 * call for copy, optionally themed around a campaign focus (POST
 * /content-calendar/generate). */
export function useGenerateCalendar() {
  const queryClient = useQueryClient();
  const { profile } = usePrimaryBusinessProfile();
  return useMutation({
    mutationFn: (payload: {
      month: string;
      platforms: string[];
      posts_per_week: number;
      campaign_focus: CampaignFocus;
      campaign_note?: string;
    }) =>
      api.post<ContentCalendarGenerateResponse>("/content-calendar/generate", {
        business_profile_id: profile!.id,
        ...payload,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["content-calendar-monthly", profile?.id] });
    },
  });
}

/** Edits one item in place (caption, hashtags, CTA, schedule, status, ...). */
export function useUpdateCalendarItem() {
  const queryClient = useQueryClient();
  const { profile } = usePrimaryBusinessProfile();
  return useMutation({
    mutationFn: ({ id, ...payload }: { id: string } & Partial<ContentCalendarItem>) =>
      api.patch<ContentCalendarItem>(`/content-calendar/${id}`, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["content-calendar-monthly", profile?.id] });
    },
  });
}

/** Rewrites just one item's copy — date/platform/type stay fixed (POST
 * /content-calendar/{id}/regenerate). */
export function useRegenerateCalendarItem() {
  const queryClient = useQueryClient();
  const { profile } = usePrimaryBusinessProfile();
  return useMutation({
    mutationFn: ({ id, instructions }: { id: string; instructions?: string }) =>
      api.post<ContentCalendarItem>(`/content-calendar/${id}/regenerate`, { instructions }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["content-calendar-monthly", profile?.id] });
    },
  });
}

export function useDeleteCalendarItem() {
  const queryClient = useQueryClient();
  const { profile } = usePrimaryBusinessProfile();
  return useMutation({
    mutationFn: (id: string) => api.delete<void>(`/content-calendar/${id}`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["content-calendar-monthly", profile?.id] });
    },
  });
}

/** Generates a visual for this post with Nano Banana (Gemini 2.5 Flash
 * Image) — free tier, additive (POST /content-calendar/{id}/generate-image). */
export function useGenerateItemImage() {
  const queryClient = useQueryClient();
  const { profile } = usePrimaryBusinessProfile();
  return useMutation({
    mutationFn: (id: string) =>
      api.post<ContentCalendarItem>(`/content-calendar/${id}/generate-image`, {}),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["content-calendar-monthly", profile?.id] });
    },
  });
}

/** Generates a video for this post with fal.ai — a real, billed API call,
 * no ongoing free tier; additive (POST /content-calendar/{id}/generate-video). */
export function useGenerateItemVideo() {
  const queryClient = useQueryClient();
  const { profile } = usePrimaryBusinessProfile();
  return useMutation({
    mutationFn: (id: string) =>
      api.post<ContentCalendarItem>(`/content-calendar/${id}/generate-video`, {}),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["content-calendar-monthly", profile?.id] });
    },
  });
}
