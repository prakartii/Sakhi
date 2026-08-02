import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { usePrimaryBusinessProfile } from "@/hooks/use-business-profile";
import { websitesQueryKey } from "@/hooks/use-websites";
import type { WebsiteChatHistoryResponse, WebsiteChatResponse } from "@/lib/types";

function websiteChatHistoryQueryKey(profileId: string | undefined) {
  return ["website-chat-history", profileId];
}

/** Website Studio's chat thread for the primary business — persisted in
 * conversation_history, keyed server-side by the business's website id. */
export function useWebsiteChatHistory() {
  const { profile, hasProfile, isLoading: profileLoading } = usePrimaryBusinessProfile();
  const query = useQuery({
    queryKey: websiteChatHistoryQueryKey(profile?.id),
    queryFn: () => api.get<WebsiteChatHistoryResponse>(`/websites/${profile!.id}/chat`),
    enabled: hasProfile && !!profile,
  });
  return {
    messages: query.data?.messages ?? [],
    isLoading: profileLoading || query.isLoading,
  };
}

/** Sends one Website Studio chat message — creates the site on the first
 * turn, refines the existing one on every turn after (POST /websites/chat). */
export function useSendWebsiteMessage() {
  const queryClient = useQueryClient();
  const { profile } = usePrimaryBusinessProfile();
  return useMutation({
    mutationFn: (message: string) =>
      api.post<WebsiteChatResponse>("/websites/chat", {
        business_profile_id: profile!.id,
        message,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: websiteChatHistoryQueryKey(profile?.id) });
      void queryClient.invalidateQueries({ queryKey: websitesQueryKey(profile?.id) });
    },
  });
}
