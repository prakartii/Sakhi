import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { usePrimaryBusinessProfile } from "@/hooks/use-business-profile";
import type { AdvisorChatHistoryResponse, AdvisorChatResponse } from "@/lib/types";

function advisorChatHistoryQueryKey(profileId: string | undefined) {
  return ["advisor-chat-history", profileId];
}

/** AI Advisor's one continuous thread for the primary business — persisted
 * in conversation_history, keyed server-side by the business's own id. */
export function useAdvisorChatHistory() {
  const { profile, hasProfile, isLoading: profileLoading } = usePrimaryBusinessProfile();
  const query = useQuery({
    queryKey: advisorChatHistoryQueryKey(profile?.id),
    queryFn: () => api.get<AdvisorChatHistoryResponse>(`/advisor/${profile!.id}/chat`),
    enabled: hasProfile && !!profile,
  });
  return {
    messages: query.data?.messages ?? [],
    isLoading: profileLoading || query.isLoading,
  };
}

/** Sends one AI Advisor message — routed through app.ai.orchestrator,
 * grounded in this business's brand/revenue/inventory/memory (POST
 * /advisor/chat). */
export function useSendAdvisorMessage() {
  const queryClient = useQueryClient();
  const { profile } = usePrimaryBusinessProfile();
  return useMutation({
    mutationFn: (message: string) =>
      api.post<AdvisorChatResponse>("/advisor/chat", {
        business_profile_id: profile!.id,
        message,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: advisorChatHistoryQueryKey(profile?.id) });
    },
  });
}
