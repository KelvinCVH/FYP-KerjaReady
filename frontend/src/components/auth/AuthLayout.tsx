import type { ReactNode } from "react";
import { Link } from "react-router";
import Logo from "@/components/Logo";

type AuthLayoutProps = {
  children: ReactNode;
};

// Shell for the Create Account and Sign In pages: logo header and one centred card
export default function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <div className="min-h-[100dvh] bg-background text-foreground">
      <a
        href="#main"
        className="sr-only focus-visible:not-sr-only focus-visible:absolute focus-visible:left-4 focus-visible:top-4 focus-visible:z-10 focus-visible:rounded-lg focus-visible:border focus-visible:border-input focus-visible:bg-card focus-visible:px-3 focus-visible:py-2 focus-visible:text-sm"
      >
        Skip to Content
      </a>

      <header className="border-b border-border">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3.5">
          <Logo />
          <Link
            to="/"
            className="rounded-md text-sm text-muted-foreground transition-colors duration-150 outline-none hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
          >
            Back to Home
          </Link>
        </div>
      </header>

      <main id="main" className="px-4 py-10 md:py-14">
        <div className="mx-auto w-full max-w-md rounded-xl border border-border bg-card p-6 md:p-8">
          {children}
        </div>
      </main>
    </div>
  );
}
