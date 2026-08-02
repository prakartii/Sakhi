import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { usePrimaryBusinessProfile } from "@/hooks/use-business-profile";
import type { MentorMatchListResponse } from "@/lib/types";

/** Mentors ranked against the business's own profile (GET /mentors/matches,
 * app.ai.rules + app.ai.explanations). Can legitimately return an empty
 * list — the mentor directory has no seed data, see the endpoint's
 * docstring — callers should render a graceful empty state, not assume a
 * match always exists. */
export function useMentorMatches() {
  const { profile, hasProfile, isLoading: profileLoading } = usePrimaryBusinessProfile();
  const query = useQuery({
    queryKey: ["mentor-matches", profile?.id],
    queryFn: () =>
      api.get<MentorMatchListResponse>("/mentors/matches", {
        business_profile_id: profile!.id,
      }),
    enabled: hasProfile && !!profile,
    retry: false,
  });
  return { ...query, isLoading: profileLoading || query.isLoading };
}
