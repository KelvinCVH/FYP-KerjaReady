import { Link } from "react-router";
import { ArrowRight, CircleCheck } from "lucide-react";
import { doneBannerText } from "@/lib/roadmapText";

// The reminder above the skills while at least one is done (KR-99), with the names in roadmap order. The status region
// stays mounted, empty when nothing is done, so screen readers hear the banner when the first skill is marked: a
// region added with its text already inside is often not announced. Emerald-50 with emerald-800 text is the DESIGN.md
// status pair for a positive state, as in FormAlert's success style.
export default function DoneSkillsBanner({ names }: { names: string[] }) {
  return (
    <div role="status">
      {names.length > 0 && (
        <div className="flex gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-emerald-800 sm:p-5">
          <CircleCheck aria-hidden="true" className="mt-0.5 size-5 shrink-0" />
          <div className="min-w-0">
            <p className="max-w-[75ch] text-base leading-relaxed break-words">{doneBannerText(names)}</p>
            {/* The ::before box makes the touch target 44px tall without changing the line */}
            <Link
              to="/candidate/resume"
              className="relative mt-2 inline-flex items-center gap-1.5 rounded-md font-medium text-primary underline underline-offset-4 outline-none before:absolute before:-inset-x-1 before:-inset-y-3 before:content-[''] hover:text-primary-hover focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-emerald-50"
            >
              Go to Resume
              <ArrowRight aria-hidden="true" className="size-4" />
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
