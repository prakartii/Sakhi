import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { usePrimaryBusinessProfile } from "@/hooks/use-business-profile";
import type { SchemeMatchListResponse } from "@/lib/types";

/** Government schemes ranked against the business's own profile
 * (GET /schemes/matches, app.ai.rules + app.ai.explanations) — not a
 * static list, see the endpoint's docstring. */
export function useSchemeMatches() {
  const { profile, hasProfile, isLoading: profileLoading } = usePrimaryBusinessProfile();
  const query = useQuery({
    queryKey: ["scheme-matches", profile?.id],
    queryFn: () =>
      api.get<SchemeMatchListResponse>("/schemes/matches", {
        business_profile_id: profile!.id,
      }),
    enabled: hasProfile && !!profile,
    retry: false, // AI-provider hiccups shouldn't hammer the endpoint on retry
  });
  return { ...query, isLoading: profileLoading || query.isLoading };
}
