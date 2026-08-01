import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { useAuth } from "@/hooks/use-auth";
import { usePrimaryBusinessProfile } from "@/hooks/use-business-profile";
import type {
  AISummary,
  InventorySummary,
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
