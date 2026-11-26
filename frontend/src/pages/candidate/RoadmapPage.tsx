import { useEffect, useRef, useState } from "react";
import { Link } from "react-router";
import { FileText, Info, Target } from "lucide-react";
import FormAlert from "@/components/auth/FormAlert";
import ProfileLoadError from "@/components/profile/ProfileLoadError";
import BuildSkillsSection from "@/components/roadmap/BuildSkillsSection";
import ImproveResumeSection from "@/components/roadmap/ImproveResumeSection";
import RegenerateDialog from "@/components/roadmap/RegenerateDialog";
import RoadmapContextCard from "@/components/roadmap/RoadmapContextCard";
import RoadmapFailed from "@/components/roadmap/RoadmapFailed";
import RoadmapSkeleton from "@/components/roadmap/RoadmapSkeleton";
import RoadmapWriting from "@/components/roadmap/RoadmapWriting";
import SkillGapEmptyState from "@/components/skill-gap/SkillGapEmptyState";
import { Button } from "@/components/ui/button";
import { usePageTitle } from "@/hooks/usePageTitle";
import { useRoadmap, type RoadmapPhase, type StartKind } from "@/hooks/useRoadmap";
import { formatDate } from "@/lib/formatDate";

const LOAD_FAILED = "We couldn’t load your learning roadmap. Check your connection, then try again.";
const AI_NOTE =
  "Written with AI from your resume assessment and this role’s job postings. AI can make mistakes, so check it " +
  "against other sources. Search links open each site’s own results, not courses KerjaReady has checked.";

// Where focus is following a run the candidate started: "pending" while its POST runs, "writing" once focus is on
// the Writing Your Roadmap heading
type FocusFollow = "none" | "pending" | "writing";

// A 503 means the database is waking up, which the API's own message says; anything else gets the page's message
function failureMessage(httpStatus: number, message: string) {
  return httpStatus === 503 ? message : LOAD_FAILED;
}

// The candidate's learning roadmap (KR-98): how to raise their lowest-rated criteria, and the skills not evidenced in
// their resume to build, written by a background AI agent from their latest assessed resume and target role.
// The first visit starts the agent on its own; the page then checks every 3 seconds until the roadmap is ready.
export default function RoadmapPage() {
  usePageTitle("Learning Roadmap | KerjaReady");

  const { load, data, phase, start, starting, startError, reload } = useRoadmap();
  const titleRef = useRef<HTMLHeadingElement>(null);
  const writingRef = useRef<HTMLHeadingElement>(null);
  const failedRef = useRef<HTMLHeadingElement>(null);
  const regenerateRef = useRef<HTMLButtonElement>(null);
  const followRef = useRef<FocusFollow>("none");
  const previousPhaseRef = useRef<RoadmapPhase | null>(null);

  // Whether this visit has shown the writing state, so the result is announced only after it
  const [sawWriting, setSawWriting] = useState(false);
  if (phase === "writing" && !sawWriting) setSawWriting(true);

  // After Try Again or Regenerate the button is gone, so focus moves to the writing heading. When writing ends,
  // focus moves on to the result, unless the candidate has moved it somewhere else meanwhile.
  useEffect(() => {
    const previous = previousPhaseRef.current;
    previousPhaseRef.current = phase;
    if (phase === previous) return;

    if (phase === "writing") {
      if (followRef.current === "pending") {
        followRef.current = "writing";
        writingRef.current?.focus();
      }
      return;
    }

    const following = followRef.current === "writing";
    followRef.current = "none";
    if (!following || previous !== "writing") return;
    const active = document.activeElement;
    if (active !== null && active !== document.body) return;
    if (phase === "done") titleRef.current?.focus();
    else if (phase === "failed") failedRef.current?.focus();
  }, [phase]);

  async function handleStart(kind: StartKind) {
    followRef.current = "pending";
    const started = await start(kind);
    if (started) return;
    followRef.current = "none";
    // The roadmap stays and the error shows under the header; the dialog has closed, so focus goes back to its button
    if (kind === "regenerate") regenerateRef.current?.focus();
  }

  let announcement = "";
  if (load.status === "loading") announcement = "Loading your learning roadmap…";
  else if (phase === "writing") announcement = "Writing your roadmap…";
  else if (phase === "done" && sawWriting) announcement = "Your roadmap is ready.";
  else if (phase === "failed" && sawWriting) announcement = "We couldn’t write your roadmap.";

  const run = phase === "done" ? data?.run : null;
  const writtenAt = run ? (run.finished_at ?? run.created_at) : null;

  function renderContent() {
    if (load.status === "loading") return <RoadmapSkeleton withContext />;
    if (load.status === "error") {
      return (
        <ProfileLoadError
          status={load.httpStatus}
          message={failureMessage(load.httpStatus, load.message)}
          onRetry={reload}
        />
      );
    }

    const { resume, target_role: role, roadmap } = load.data;

    if (phase === "no-resume" || !resume) {
      return (
        <SkillGapEmptyState
          icon={<FileText aria-hidden="true" />}
          action={
            <Button asChild>
              <Link to="/candidate/resume">Go to Resume</Link>
            </Button>
          }
        >
          Your learning roadmap starts from an assessed resume. Upload one, or wait for the current assessment to
          finish.
        </SkillGapEmptyState>
      );
    }

    if (phase === "no-role" || !role) {
      return (
        <SkillGapEmptyState
          icon={<Target aria-hidden="true" />}
          action={
            <Button asChild>
              <Link to="/candidate/profile">Choose Target Role</Link>
            </Button>
          }
        >
          Choose a target role on your Profile to get a learning roadmap for it.
        </SkillGapEmptyState>
      );
    }

    if (phase === "writing") {
      return (
        <>
          <RoadmapContextCard role={role} resume={resume} showChangeLink={false} />
          <div className="mt-6">
            <RoadmapWriting headingRef={writingRef} />
          </div>
          <div className="mt-10">
            <RoadmapSkeleton still />
          </div>
        </>
      );
    }

    if (phase === "failed" || !roadmap || !run) {
      return (
        <>
          <RoadmapContextCard role={role} resume={resume} showChangeLink />
          <div className="mt-6">
            <RoadmapFailed
              headingRef={failedRef}
              error={startError?.kind === "start" ? startError.message : null}
              starting={starting}
              onRetry={() => void handleStart("start")}
            />
          </div>
        </>
      );
    }

    return (
      <>
        <RoadmapContextCard role={role} resume={resume} showChangeLink />
        <p className="mt-6 flex items-start gap-2 text-sm leading-relaxed text-muted-foreground">
          <Info aria-hidden="true" className="mt-0.5 size-4 shrink-0" />
          {AI_NOTE}
        </p>
        {roadmap.resume_steps.length > 0 && (
          <div className="mt-10">
            <ImproveResumeSection steps={roadmap.resume_steps} />
          </div>
        )}
        <div className="mt-10">
          <BuildSkillsSection key={run.run_id} milestones={roadmap.skill_milestones} />
        </div>
      </>
    );
  }

  return (
    <div className="max-w-5xl">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between sm:gap-8">
        <div className="min-w-0">
          <h1
            ref={titleRef}
            tabIndex={-1}
            className="rounded-md text-2xl font-semibold text-balance outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
          >
            Learning Roadmap
          </h1>
          <p className="mt-2 max-w-[65ch] text-base leading-relaxed text-muted-foreground">
            Steps to strengthen your resume and build the skills your target role asks for, based on your latest
            assessment.
          </p>
        </div>
        {writtenAt && (
          <div className="flex shrink-0 flex-col items-start gap-1.5 sm:items-end">
            <RegenerateDialog
              triggerRef={regenerateRef}
              starting={starting}
              onConfirm={() => void handleStart("regenerate")}
            />
            <p className="text-sm text-muted-foreground">
              Written <time dateTime={writtenAt}>{formatDate(writtenAt)}</time>
            </p>
          </div>
        )}
      </div>
      <p role="status" className="sr-only">
        {announcement}
      </p>
      {phase === "done" && startError?.kind === "regenerate" && (
        <div className="mt-4">
          <FormAlert message={startError.message} />
        </div>
      )}
      <div className="mt-6">{renderContent()}</div>
    </div>
  );
}
