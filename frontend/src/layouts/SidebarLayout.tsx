import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router";
import { signOut } from "aws-amplify/auth";
import { LoaderCircle, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";

export type NavItem = { label: string; to: string };

type SidebarLayoutProps = { navItems: NavItem[] };

export default function SidebarLayout({ navItems }: SidebarLayoutProps) {
  const navigate = useNavigate();
  const [signingOut, setSigningOut] = useState(false);

  async function handleSignOut() {
    if (signingOut) return;
    setSigningOut(true);
    try {
      // Google users leave through Cognito's /logout, which returns to /sign-in
      await signOut();
    } catch {
      // Amplify clears the local session even when revoking the token fails
    }
    navigate("/sign-in", { replace: true });
  }

  return (
    <div className="flex min-h-screen bg-gray-50 text-gray-900">
      <aside className="flex w-56 shrink-0 flex-col border-r border-gray-200 bg-white p-4">
        <p className="mb-6 text-lg font-semibold">KerjaReady</p>
        <nav className="flex flex-col gap-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `rounded-md px-3 py-2 text-sm ${
                  isActive ? "bg-gray-900 text-white" : "text-gray-700 hover:bg-gray-100"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <Button
          type="button"
          variant="ghost"
          onClick={handleSignOut}
          disabled={signingOut}
          className="mt-auto w-full justify-start px-3 text-muted-foreground hover:text-foreground"
        >
          {signingOut ? (
            <LoaderCircle aria-hidden="true" className="animate-spin" />
          ) : (
            <LogOut aria-hidden="true" />
          )}
          Sign Out
        </Button>
      </aside>
      <main className="flex-1 p-8">
        <Outlet />
      </main>
    </div>
  );
}
