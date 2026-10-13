import { Search, TrendingUp, Upload } from "lucide-react";
import FadeUp from "./FadeUp";
import { container, sectionHeading, sectionSpacing } from "./styles";

const steps = [
  {
    icon: Upload,
    title: "Upload",
    description: "Upload your resume. KerjaReady reads the text and finds the skills it shows.",
  },
  {
    icon: Search,
    title: "Assess",
    description:
      "Choose a target role and see which of its required skills are evidenced in your resume.",
  },
  {
    icon: TrendingUp,
    title: "Improve",
    description:
      "Get recommendations tied to lines in your resume and a learning roadmap for the rest.",
  },
];

export default function HowItWorksSection() {
  return (
    <section
      id="how-it-works"
      aria-labelledby="how-it-works-heading"
      className={`border-y border-border bg-card ${sectionSpacing}`}
    >
      <FadeUp className={container}>
        <h2 id="how-it-works-heading" className={sectionHeading}>
          How It Works
        </h2>
        <p className="mt-3 max-w-[65ch] text-base leading-relaxed text-muted-foreground">
          From your first upload to a clear plan in three steps.
        </p>

        <ol className="mt-12 grid gap-10 md:grid-cols-3 md:gap-8">
          {steps.map((step, index) => (
            <li
              key={step.title}
              className={`border-t-2 pt-6 ${index === 0 ? "border-primary" : "border-border"}`}
            >
              <span className="flex size-10 items-center justify-center rounded-lg bg-primary-subtle text-primary">
                <step.icon aria-hidden="true" className="size-5" />
              </span>
              <h3 className="mt-5 text-lg font-semibold">{step.title}</h3>
              <p className="mt-2 max-w-[65ch] text-base leading-relaxed text-muted-foreground">
                {step.description}
              </p>
            </li>
          ))}
        </ol>
      </FadeUp>
    </section>
  );
}
