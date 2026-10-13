import { Info, Lock, MapPin } from "lucide-react";
import FadeUp from "./FadeUp";
import { container, sectionHeading, sectionSpacing } from "./styles";

const commitments = [
  {
    icon: Lock,
    title: "Private by Default",
    description: "Recruiters see your resume only after you apply to their listing.",
  },
  {
    icon: MapPin,
    title: "Grounded in Local Data",
    description: "Role requirements are drawn from Malaysian technology job postings.",
  },
  {
    icon: Info,
    title: "Signals, Not Verdicts",
    description:
      "Results show what your resume evidences. They support decisions and do not judge a person’s ability.",
  },
];

export default function FairAndPrivateSection() {
  return (
    <section
      aria-labelledby="fair-private-heading"
      className={`border-y border-border bg-card ${sectionSpacing}`}
    >
      <FadeUp className={`${container} grid gap-10 md:grid-cols-5 md:gap-12`}>
        <div className="md:col-span-2">
          <h2 id="fair-private-heading" className={sectionHeading}>
            Built to Be Fair and Private
          </h2>
          <p className="mt-3 max-w-[65ch] text-base leading-relaxed text-muted-foreground">
            KerjaReady handles personal data and career decisions, so it works within clear limits.
          </p>
        </div>

        <ul className="divide-y divide-border md:col-span-3">
          {commitments.map((item) => (
            <li key={item.title} className="flex gap-4 py-6 first:pt-0 last:pb-0">
              <span className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-muted text-foreground">
                <item.icon aria-hidden="true" className="size-5" />
              </span>
              <div>
                <h3 className="text-base font-semibold">{item.title}</h3>
                <p className="mt-1 max-w-[65ch] text-sm leading-relaxed text-muted-foreground">
                  {item.description}
                </p>
              </div>
            </li>
          ))}
        </ul>
      </FadeUp>
    </section>
  );
}
