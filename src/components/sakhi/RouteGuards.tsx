import { useEffect, type ReactNode } from "react";
import { useNavigate } from "@tanstack/react-router";
import { Loader2 } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { usePrimaryBusinessProfile } from "@/hooks/use-business-profile";

function CenteredSpinner() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
    </div>
  );
}

/** Session lives in browser localStorage, invisible during SSR, so this
 * check only ever runs client-side after hydration — wrapping a route's
 * component (not a loader/beforeLoad) is what makes that safe: a
 * logged-in user's first paint briefly shows the spinner instead of being
 * incorrectly bounced to /login by a server render that can't see their
 * session yet. */
export function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!loading && !user) {
      navigate({ to: "/login" });
    }
  }, [loading, user, navigate]);

  if (loading || !user) {
    return <CenteredSpinner />;
  }
  return <>{children}</>;
}

/** Gates a route on "does the signed-in user have a business profile yet."
 * `redirectWhen` picks the direction: "missing" sends a profile-less user
 * to onboarding (used by /dashboard and the other app pages); "present"
 * sends an already-onboarded user away from the onboarding wizard. */
export function RequireBusinessProfile({
  children,
  redirectWhen,
  redirectTo,
}: {
  children: ReactNode;
  redirectWhen: "missing" | "present";
  redirectTo: string;
}) {
  const { isLoading, hasProfile } = usePrimaryBusinessProfile();
  const navigate = useNavigate();

  const shouldRedirect =
    !isLoading && (redirectWhen === "missing" ? !hasProfile : hasProfile);

  useEffect(() => {
    if (shouldRedirect) {
      navigate({ to: redirectTo });
    }
  }, [shouldRedirect, navigate, redirectTo]);

  if (isLoading || shouldRedirect) {
    return <CenteredSpinner />;
  }
  return <>{children}</>;
}
