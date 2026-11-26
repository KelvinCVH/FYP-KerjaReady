import { Link } from "react-router";

// The inline "Change on Profile" link under a target role, for a card on a white surface.
// The ::before box makes the touch target 44px tall without changing the line.
export default function ChangeOnProfileLink() {
  return (
    <Link
      to="/candidate/profile"
      className="relative rounded-md font-medium text-primary underline-offset-4 outline-none before:absolute before:-inset-x-1 before:-inset-y-3.5 before:content-[''] hover:underline focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-card"
    >
      Change on Profile
    </Link>
  );
}
