import { Link } from "react-router";
import { inlineLink } from "./authFormClasses";

export default function SignInPrompt() {
  return (
    <p className="mt-6 text-center text-sm text-muted-foreground">
      Already have an account?{" "}
      <Link to="/sign-in" className={`font-medium ${inlineLink}`}>
        Sign In
      </Link>
    </p>
  );
}
