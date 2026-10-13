import { Link } from "react-router";
import { container, focusRing } from "./styles";

const currentYear = new Date().getFullYear();

const footerLinks = [
  { label: "Privacy Notice", to: "/privacy" },
  { label: "Sign In", to: "/sign-in" },
];

export default function LandingFooter() {
  return (
    <footer className={`${container} flex flex-col gap-6 py-10 sm:flex-row sm:items-start sm:justify-between`}>
      <div>
        <p translate="no" className="font-semibold">KerjaReady</p>
        <p className="mt-1 text-sm text-muted-foreground">© {currentYear} KerjaReady</p>
      </div>

      <nav aria-label="Footer">
        <ul className="flex gap-6">
          {footerLinks.map((link) => (
            <li key={link.to}>
              <Link
                to={link.to}
                className={`text-sm text-muted-foreground transition-colors duration-150 hover:text-foreground ${focusRing}`}
              >
                {link.label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </footer>
  );
}
