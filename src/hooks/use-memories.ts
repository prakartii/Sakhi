import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { usePrimaryBusinessProfile } from "@/hooks/use-business-profile";
import type {
  BusinessMemoryListResponse,
  MemoryInsightsResponse,
  MemorySearchResponse,
} from "@/lib/types";

export function useBusinessMemories() {
  const { profile, hasProfile, isLoading: profileLoading } = usePrimaryBusinessProfile();
  const query = useQuery({
    queryKey: ["business-memories", profile?.id],
    queryFn: () =>
      api.get<BusinessMemoryListResponse>("/business-memories", {
        business_profile_id: profile!.id,
        limit: 50,
      }),
    enabled: hasProfile && !!profile,
  });
  return { ...query, isLoading: profileLoading || query.isLoading, profile };
}

/** A narrated "Why" over the business's own memory stats
 * (GET /business-memories/insights, app.ai.explanations). */
export function useMemoryInsights() {
  const { profile, hasProfile, isLoading: profileLoading } = usePrimaryBusinessProfile();
  const query = useQuery({
    queryKey: ["business-memory-insights", profile?.id],
    queryFn: () =>
      api.get<MemoryInsightsResponse>("/business-memories/insights", {
        business_profile_id: profile!.id,
      }),
    enabled: hasProfile && !!profile,
    retry: false, // AI-provider hiccups shouldn't hammer the endpoint on retry
  });
  return { ...query, isLoading: profileLoading || query.isLoading };
}

/** Semantic search over the business's memories — ranked by pgvector
 * cosine similarity in Postgres (GET /business-memories/search), not a
 * substring match. Disabled until a non-empty query is provided. */
export function useSearchMemories(searchQuery: string) {
  const { profile, hasProfile } = usePrimaryBusinessProfile();
  const trimmed = searchQuery.trim();
  return useQuery({
    queryKey: ["business-memory-search", profile?.id, trimmed],
    queryFn: () =>
      api.get<MemorySearchResponse>("/business-memories/search", {
        business_profile_id: profile!.id,
        query: trimmed,
        k: 5,
      }),
    enabled: hasProfile && !!profile && trimmed.length > 0,
  });
}
