import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { usePrimaryBusinessProfile } from "@/hooks/use-business-profile";
import type { SocialMediaConnectionListResponse, SocialPlatform } from "@/lib/types";

function connectionsQueryKey(profileId: string | undefined) {
  return ["social-connections", profileId];
}

/** Connected platform accounts for the primary business
 * (GET /social-connections). No OAuth flow exists in this app yet — see
 * useConnectAccount's docstring — so this is a manual token entry, not a
 * "Sign in with Instagram" popup. */
export function useSocialConnections() {
  const { profile, hasProfile, isLoading: profileLoading } = usePrimaryBusinessProfile();
  const query = useQuery({
    queryKey: connectionsQueryKey(profile?.id),
    queryFn: () =>
      api.get<SocialMediaConnectionListResponse>("/social-connections", {
        business_profile_id: profile!.id,
      }),
    enabled: hasProfile && !!profile,
  });
  return {
    items: query.data?.items ?? [],
    isLoading: profileLoading || query.isLoading,
  };
}

/** Records an access token obtained elsewhere — this app has no real Meta
 * Developer app / Instagram Graph API credentials, so there is no working
 * "Connect with Instagram" OAuth popup to launch. See
 * social_media_connections.py's module docstring on the backend. */
export function useConnectAccount() {
  const queryClient = useQueryClient();
  const { profile } = usePrimaryBusinessProfile();
  return useMutation({
    mutationFn: (payload: {
      platform: SocialPlatform;
      account_name?: string | undefined;
      access_token: string;
    }) =>
      api.post("/social-connections", {
        business_profile_id: profile!.id,
        ...payload,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: connectionsQueryKey(profile?.id) });
    },
  });
}

export function useDisconnectAccount() {
  const queryClient = useQueryClient();
  const { profile } = usePrimaryBusinessProfile();
  return useMutation({
    mutationFn: (connectionId: string) =>
      api.post(`/social-connections/${connectionId}/disconnect`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: connectionsQueryKey(profile?.id) });
    },
  });
}
