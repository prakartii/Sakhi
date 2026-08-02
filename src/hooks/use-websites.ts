import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { usePrimaryBusinessProfile } from "@/hooks/use-business-profile";
import type { Website, WebsiteGenerateResponse, WebsiteListResponse } from "@/lib/types";

export function websitesQueryKey(profileId: string | undefined) {
  return ["websites", profileId];
}

/** The primary business's most recent website record (metadata only — the
 * generated page copy itself isn't persisted, see /websites/generate's
 * docstring, so it's only available right after a generate/regenerate
 * call). */
export function usePrimaryWebsite() {
  const { profile, hasProfile, isLoading: profileLoading } = usePrimaryBusinessProfile();
  const query = useQuery({
    queryKey: websitesQueryKey(profile?.id),
    queryFn: () =>
      api.get<WebsiteListResponse>("/websites", {
        business_profile_id: profile!.id,
        limit: 1,
      }),
    enabled: hasProfile && !!profile,
  });
  return {
    website: query.data?.items[0],
    isLoading: profileLoading || query.isLoading,
    profile,
  };
}

/** Generates (first time) or regenerates (every time after) the primary
 * business's website from its brand kit — POST /websites/generate. */
export function useGenerateWebsite() {
  const queryClient = useQueryClient();
  const { profile } = usePrimaryBusinessProfile();
  return useMutation({
    mutationFn: () =>
      api.post<WebsiteGenerateResponse>("/websites/generate", {
        business_profile_id: profile!.id,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: websitesQueryKey(profile?.id) });
    },
  });
}

export function usePublishWebsite(websiteId: string | undefined) {
  const queryClient = useQueryClient();
  const { profile } = usePrimaryBusinessProfile();
  return useMutation({
    mutationFn: () => api.patch<Website>(`/websites/${websiteId}`, { published: true }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: websitesQueryKey(profile?.id) });
    },
  });
}
