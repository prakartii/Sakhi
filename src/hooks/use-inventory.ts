import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { usePrimaryBusinessProfile } from "@/hooks/use-business-profile";
import type { InventoryItem, InventoryListResponse, InventorySummary } from "@/lib/types";

function inventoryQueryKey(profileId: string | undefined) {
  return ["inventory", profileId];
}
function inventorySummaryQueryKey(profileId: string | undefined) {
  return ["inventory-summary", profileId];
}

export function useInventoryList() {
  const { profile, hasProfile, isLoading: profileLoading } = usePrimaryBusinessProfile();
  const query = useQuery({
    queryKey: inventoryQueryKey(profile?.id),
    queryFn: () =>
      api.get<InventoryListResponse>("/inventory", {
        business_profile_id: profile!.id,
        limit: 50,
      }),
    enabled: hasProfile && !!profile,
  });
  return { ...query, isLoading: profileLoading || query.isLoading, profile };
}

/** Same summary data dashboard.tsx already fetches (see use-dashboard-data)
 * — kept here too so the Inventory page doesn't depend on a dashboard-only
 * hook module. React Query dedupes both under the same query key. */
export function useInventorySummary() {
  const { profile, hasProfile } = usePrimaryBusinessProfile();
  return useQuery({
    queryKey: inventorySummaryQueryKey(profile?.id),
    queryFn: () =>
      api.get<InventorySummary>("/inventory/summary", {
        business_profile_id: profile!.id,
      }),
    enabled: hasProfile && !!profile,
  });
}

export function useCreateInventoryItem() {
  const queryClient = useQueryClient();
  const { profile } = usePrimaryBusinessProfile();
  return useMutation({
    mutationFn: (payload: {
      item_name: string;
      unit?: string;
      reorder_level?: number;
      unit_cost?: number;
      selling_price?: number;
      current_quantity?: number;
      category?: string;
    }) =>
      api.post<InventoryItem>("/inventory", {
        business_profile_id: profile!.id,
        ...payload,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: inventoryQueryKey(profile?.id) });
      void queryClient.invalidateQueries({ queryKey: inventorySummaryQueryKey(profile?.id) });
    },
  });
}

export function useStockAction(inventoryId: string) {
  const queryClient = useQueryClient();
  const { profile } = usePrimaryBusinessProfile();
  return useMutation({
    mutationFn: (payload: { direction: "in" | "out"; quantity: number; notes?: string }) =>
      api.post<InventoryItem>(`/inventory/${inventoryId}/stock-${payload.direction}`, {
        quantity: payload.quantity,
        notes: payload.notes,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: inventoryQueryKey(profile?.id) });
      void queryClient.invalidateQueries({ queryKey: inventorySummaryQueryKey(profile?.id) });
    },
  });
}
