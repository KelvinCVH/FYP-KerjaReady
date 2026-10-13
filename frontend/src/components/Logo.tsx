import { Link } from "react-router";

// KerjaReady wordmark linking home. Used by the landing and auth headers.
export default function Logo() {
  return (
    <Link
      to="/"
      className="flex items-center gap-2 rounded-md text-lg font-semibold outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
    >
      <span
        aria-hidden="true"
        className="flex size-7 items-center justify-center rounded-md bg-primary text-sm text-primary-foreground"
      >
        K
      </span>
      <span translate="no">KerjaReady</span>
    </Link>
  );
}
