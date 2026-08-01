import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { usePrimaryBusinessProfile } from "@/hooks/use-business-profile";
import type { BusinessMemoryListResponse } from "@/lib/types";

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
