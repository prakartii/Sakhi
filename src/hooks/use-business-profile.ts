import { useQuery, useQueryClient, type UseQueryResult } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { useAuth } from "@/hooks/use-auth";
import type { BusinessProfile, BusinessProfileListResponse } from "@/lib/types";

export const businessProfilesQueryKey = (userId: string | undefined) => [
  "business-profiles",
  userId,
];

/** The signed-in user's business profiles. Enabled only once a session
 * exists — see use-auth's `loading` flag for why that matters during SSR. */
export function useBusinessProfiles(): UseQueryResult<BusinessProfileListResponse> {
  const { user, loading } = useAuth();
  return useQuery({
    queryKey: businessProfilesQueryKey(user?.id),
    queryFn: () => api.get<BusinessProfileListResponse>("/business-profiles"),
    enabled: !loading && !!user,
  });
}

/** Convenience accessor for the primary (or first) profile — every current
 * page in this app operates on a single active business, not a picker. */
export function usePrimaryBusinessProfile(): {
  profile: BusinessProfile | undefined;
  isLoading: boolean;
  hasProfile: boolean;
} {
  const query = useBusinessProfiles();
  // GET /business-profiles returns every status (including archived) unless
  // filtered — an archived profile must never count as "the user's active
  // business" or RequireBusinessProfile would never send them back to
  // /business-setup to onboard a replacement.
  const items = (query.data?.items ?? []).filter((p) => p.status !== "archived");
  const profile = items.find((p) => p.is_primary) ?? items[0];
  return {
    profile,
    isLoading: query.isLoading,
    hasProfile: items.length > 0,
  };
}

export function useInvalidateBusinessProfiles() {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  return () => queryClient.invalidateQueries({ queryKey: businessProfilesQueryKey(user?.id) });
}
