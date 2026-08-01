import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { usePrimaryBusinessProfile } from "@/hooks/use-business-profile";
import type { Transaction, TransactionListResponse } from "@/lib/types";

function transactionsQueryKey(profileId: string | undefined) {
  return ["transactions", profileId];
}

export function useTransactions() {
  const { profile, hasProfile, isLoading: profileLoading } = usePrimaryBusinessProfile();
  const query = useQuery({
    queryKey: transactionsQueryKey(profile?.id),
    queryFn: () =>
      api.get<TransactionListResponse>("/transactions", {
        business_profile_id: profile!.id,
        limit: 100,
      }),
    enabled: hasProfile && !!profile,
  });
  return { ...query, isLoading: profileLoading || query.isLoading, profile };
}

export function useCreateTransaction() {
  const queryClient = useQueryClient();
  const { profile } = usePrimaryBusinessProfile();
  return useMutation({
    mutationFn: (payload: {
      transaction_type: "income" | "expense";
      amount: number;
      category?: string;
      description?: string;
    }) =>
      api.post<Transaction>("/transactions", {
        business_profile_id: profile!.id,
        ...payload,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: transactionsQueryKey(profile?.id) });
    },
  });
}
