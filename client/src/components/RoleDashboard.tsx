/**
 * Role dashboard guard: only a backend-authenticated user can render a workspace,
 * and a mismatched dashboard URL is redirected to that user's own role dashboard.
 */
import { useSession } from "@/contexts/SessionContext";
import { type Role } from "@/services/api";
import { useEffect } from "react";
import { useLocation } from "wouter";
import Dashboard from "@/pages/Dashboard";

export default function RoleDashboard({ requiredRole }: { requiredRole?: Role }) {
  const { user, ready } = useSession();
  const [, navigate] = useLocation();

  useEffect(() => {
    if (!ready) return;
    if (!user) {
      navigate(requiredRole ? `/sign-in/${requiredRole}` : "/sign-in");
      return;
    }
    if (requiredRole && user.role !== requiredRole) navigate(`/dashboard/${user.role}`);
  }, [navigate, ready, requiredRole, user]);

  if (!ready || !user || (requiredRole && user.role !== requiredRole)) return <div className="min-h-screen bg-[#F6F4EE]" />;
  return <Dashboard />;
}
