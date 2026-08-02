import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { useAuth } from "@/hooks/use-auth";
import { usePrimaryBusinessProfile } from "@/hooks/use-business-profile";
import type {
  AISummary,
  GrowthForecast,
  InventorySummary,
  NoticedSummary,
  NotificationListResponse,
  ScheduledPostListResponse,
} from "@/lib/types";

export function useInventorySummary() {
  const { profile, hasProfile } = usePrimaryBusinessProfile();
  return useQuery({
    queryKey: ["inventory-summary", profile?.id],
    queryFn: () =>
      api.get<InventorySummary>("/inventory/summary", {
        business_profile_id: profile!.id,
      }),
    enabled: hasProfile && !!profile,
  });
}

export function useNotifications() {
  const { user, loading } = useAuth();
  return useQuery({
    queryKey: ["notifications", user?.id],
    queryFn: () =>
      api.get<NotificationListResponse>("/notifications", { limit: 10, status: "unread" }),
    enabled: !loading && !!user,
  });
}

export function useScheduledPostsQueue() {
  const { profile, hasProfile } = usePrimaryBusinessProfile();
  return useQuery({
    queryKey: ["scheduled-posts-queue", profile?.id],
    queryFn: () =>
      api.get<ScheduledPostListResponse>("/scheduled-posts/queue", {
        business_profile_id: profile!.id,
        limit: 10,
      }),
    enabled: hasProfile && !!profile,
  });
}

export function useAISummary() {
  const { profile, hasProfile } = usePrimaryBusinessProfile();
  return useQuery({
    queryKey: ["ai-summary", profile?.id],
    queryFn: () => api.get<AISummary>(`/business-profiles/${profile!.id}/ai-summary`),
    enabled: hasProfile && !!profile,
    retry: false,
  });
}

/** Weekly revenue trend + linear-regression future projection
 * (GET /business-profiles/{id}/growth-forecast, app.ai.forecasting.run_rate
 * — deterministic, not an LLM call for the numbers themselves). */
export function useGrowthForecast() {
  const { profile, hasProfile } = usePrimaryBusinessProfile();
  return useQuery({
    queryKey: ["growth-forecast", profile?.id],
    queryFn: () => api.get<GrowthForecast>(`/business-profiles/${profile!.id}/growth-forecast`),
    enabled: hasProfile && !!profile,
    retry: false,
  });
}

/** Cross-module proactive signals — stock, revenue decline, memory
 * challenges, connected in one narrative when more than one applies
 * (GET /business-profiles/{id}/noticed-summary). Deliberately excludes
 * scheme matches — see GET /schemes/matches for those. */
export function useNoticedSummary() {
  const { profile, hasProfile } = usePrimaryBusinessProfile();
  return useQuery({
    queryKey: ["noticed-summary", profile?.id],
    queryFn: () => api.get<NoticedSummary>(`/business-profiles/${profile!.id}/noticed-summary`),
    enabled: hasProfile && !!profile,
    retry: false,
  });
}
