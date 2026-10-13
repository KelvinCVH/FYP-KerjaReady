import { Link } from "react-router";
import Logo from "@/components/Logo";
import { Button } from "@/components/ui/button";
import { focusRing } from "./styles";

const navLinks = [
  { label: "How It Works", href: "#how-it-works" },
  { label: "For Students", href: "#for-students" },
  { label: "For Recruiters", href: "#for-recruiters" },
];

export default function LandingHeader() {
  return (
    <header className="border-b border-border">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-2 px-4 py-4 md:px-8">
        <Logo />

        <nav aria-label="Main" className="hidden md:block">
          <ul className="flex items-center gap-8">
            {navLinks.map((link) => (
              <li key={link.href}>
                <a
                  href={link.href}
                  className={`text-sm text-muted-foreground transition-colors duration-150 hover:text-foreground ${focusRing}`}
                >
                  {link.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        <div className="flex items-center gap-1 md:gap-3">
          <Button asChild variant="ghost" className="px-3">
            <Link to="/sign-in">Sign In</Link>
          </Button>
          <Button asChild className="px-3 md:px-4">
            <Link to="/register">Create Account</Link>
          </Button>
        </div>
      </div>
    </header>
  );
}
