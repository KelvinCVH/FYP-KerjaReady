import { Link } from "react-router";
import { Button } from "@/components/ui/button";
import ExampleResultCard from "./ExampleResultCard";
import FadeUp from "./FadeUp";
import { container } from "./styles";

export default function HeroSection() {
  return (
    <section aria-labelledby="hero-heading" className="pt-16 pb-20 md:pt-24 md:pb-28">
      <FadeUp className={`${container} grid items-center gap-12 lg:grid-cols-2 lg:gap-16`}>
        <div>
          <h1
            id="hero-heading"
            className="text-4xl font-semibold tracking-tight md:text-5xl lg:text-6xl"
          >
            Know Where Your Resume Stands
          </h1>
          <p className="mt-6 max-w-[65ch] text-lg leading-relaxed text-muted-foreground">
            Compare your resume with Malaysian tech job postings, see which skills are evidenced,
            and get a roadmap for the rest.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button asChild size="lg">
              <Link to="/register?role=candidate">Assess My Resume</Link>
            </Button>
            <Button asChild variant="outline" size="lg">
              <Link to="/register?role=recruiter">Find Candidates</Link>
            </Button>
          </div>
        </div>

        <ExampleResultCard />
      </FadeUp>
    </section>
  );
}
