import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router";
import { Clock, FileText, Info, Target, Upload } from "lucide-react";
import ProfileLoadError from "@/components/profile/ProfileLoadError";
import { profileCard } from "@/components/profile/styles";
import ResumeNotFound from "@/components/resume/ResumeNotFound";
import SkillColumn from "@/components/skill-gap/SkillColumn";
import SkillGapContextCard, { type SkillCounts } from "@/components/skill-gap/SkillGapContextCard";
import SkillGapEmptyState from "@/components/skill-gap/SkillGapEmptyState";
import SkillGapSkeleton from "@/components/skill-gap/SkillGapSkeleton";
import { Button } from "@/components/ui/button";
import { useApiData } from "@/hooks/useApiData";
import { usePageTitle } from "@/hooks/usePageTitle";
import { useSkillGap } from "@/hooks/useSkillGap";
import { listResumes } from "@/lib/resumeApi";
import type { SkillGap } from "@/lib/skillGapApi";

const LOAD_FAILED = "We couldn’t load your skill gap analysis. Check your connection, then try again.";
const MATCHING_NOTE =
  "Skills are found by automated matching of your resume text, so a skill described in unusual words can be missed. " +
  "A skill that is not evidenced is one this resume does not show, not one you lack.";
const LATEST_PATH = "/candidate/skill-gap";

// The resume in the URL: null for the newest assessed one, false when it is not a whole number
function parseResumeId(param: string | undefined) {
  if (param === undefined) return null;
  return /^\d+$/.test(param) ? Number(param) : false;
}

// A 503 means the database is waking up, which the API's own message says; anything else gets the page's message
function failureMessage(httpStatus: number, message: string) {
  return httpStatus === 503 ? message : LOAD_FAILED;
}

// The target role's skills, split by whether the candidate's resume evidences them (KR-94).
// /candidate/skill-gap compares the newest assessed resume; /candidate/skill-gap/<id> compares that one.
// The target role is the one saved on Profile; this page only shows it.
export default function SkillGapPage() {
  usePageTitle("Skill Gap | KerjaReady");

  const { resumeId: param } = useParams();
  const navigate = useNavigate();
  const urlId = parseResumeId(param);
  const { state: list, retry: retryList } = useApiData(listResumes);
  // Only assessed resumes have matched skills. The API lists newest first.
  const assessed = list.status === "ready" ? list.data.filter((resume) => resume.status === "done") : null;

  // The resume compared: the one in the URL, or the newest assessed one once the list is in.
  // With an id, the list and the skill gap load at the same time.
  let selectedId: number | null = null;
  if (typeof urlId === "number") selectedId = urlId;
  else if (urlId === null && assessed) selectedId = assessed[0]?.resume_id ?? null;
  const { state: gap, lastRole, retry: retryGap } = useSkillGap(selectedId);

  // The first resume shown, and whether the candidate has switched since, so only a switch is announced
  const [firstId, setFirstId] = useState<number | null>(null);
  const [switched, setSwitched] = useState(false);
  if (firstId === null && selectedId !== null) setFirstId(selectedId);
  if (!switched && firstId !== null && selectedId !== null && selectedId !== firstId) setSwitched(true);

  // While a switch loads or fails, the context card stays with the role from the last result
  const keepCard = assessed !== null && selectedId !== null && lastRole !== null;
  const loadingAll =
    urlId !== false &&
    list.status !== "error" &&
    gap.status !== "error" &&
    (list.status === "loading" || (gap.status === "loading" && !keepCard));

  let announcement = "";
  if (loadingAll) announcement = "Loading your skill gap analysis…";
  else if (switched && gap.status === "ready") {
    const shown = assessed?.find((resume) => resume.resume_id === gap.resumeId);
    announcement = `Showing the skill gap for ${shown ? shown.file_name : "an earlier resume"}.`;
  }

  // Try Again runs only the requests that failed
  function retryFailed() {
    if (list.status === "error") retryList();
    if (gap.status === "error") retryGap();
  }

  function renderContent() {
    if (urlId === false) return <ResumeNotFound latestTo={LATEST_PATH} />;

    if (gap.status === "error" && gap.httpStatus === 404) {
      return <ResumeNotFound message={gap.message} latestTo={LATEST_PATH} />;
    }
    if (gap.status === "error" && gap.httpStatus === 409) {
      return (
        <SkillGapEmptyState
          tone="neutral"
          icon={<Clock aria-hidden="true" />}
          action={
            <Button asChild>
              <Link to={`/candidate/resume/${gap.resumeId}`}>View Assessment</Link>
            </Button>
          }
        >
          This resume doesn’t have a finished assessment, so there’s no skill gap to show.
        </SkillGapEmptyState>
      );
    }
    if (list.status === "error") {
      return (
        <ProfileLoadError status={list.httpStatus} message={failureMessage(list.httpStatus, list.message)} onRetry={retryFailed} />
      );
    }
    if (gap.status === "error" && !keepCard) {
      return (
        <ProfileLoadError status={gap.httpStatus} message={failureMessage(gap.httpStatus, gap.message)} onRetry={retryFailed} />
      );
    }
    if (loadingAll || assessed === null) return <SkillGapSkeleton />;

    // No assessed resume to compare: the skill gap API isn't called
    if (selectedId === null) {
      return (
        <SkillGapEmptyState
          icon={<FileText aria-hidden="true" />}
          action={
            <Button asChild>
              <Link to="/candidate/resume">
                <Upload aria-hidden="true" />
                Upload Resume
              </Link>
            </Button>
          }
        >
          Upload your resume to see which skills for your target role are evidenced in it.
        </SkillGapEmptyState>
      );
    }

    if (gap.status === "ready" && gap.data.target_role === null) {
      return (
        <SkillGapEmptyState
          icon={<Target aria-hidden="true" />}
          action={
            <Button asChild>
              <Link to="/candidate/profile">Choose Target Role</Link>
            </Button>
          }
        >
          Choose a target role on your Profile to see which of its skills are evidenced in your resume.
        </SkillGapEmptyState>
      );
    }

    // From here on there is a role: this result's, or the last one's while a switch loads or has failed
    const result = gap.status === "ready" ? gap.data : null;
    const role = result?.target_role ?? lastRole;
    if (!role) return <SkillGapSkeleton />;

    let counts: SkillCounts = null;
    if (result) counts = { evidenced: result.evidenced.length, total: result.evidenced.length + result.not_evidenced.length };
    else if (gap.status === "loading") counts = "loading";

    return (
      <>
        <SkillGapContextCard
          targetRole={role}
          counts={counts}
          resumes={assessed}
          selectedId={selectedId}
          onSelect={(resumeId) => navigate(`${LATEST_PATH}/${resumeId}`)}
        />
        {renderColumns(result, role.title, role.posting_count)}
      </>
    );
  }

  // result is null while a switch loads or after it failed
  function renderColumns(result: SkillGap | null, title: string, postingCount: number) {
    if (result && result.evidenced.length + result.not_evidenced.length === 0) {
      return (
        <div className={`${profileCard} mt-6`}>
          <p className="text-sm text-muted-foreground">
            There isn’t enough job posting data to list skills for {title} yet.
          </p>
        </div>
      );
    }

    let columns;
    if (result) {
      // Keyed by resume, so Show All and open rows start closed for each resume
      columns = (
        <div key={result.resume_id} className="grid grid-cols-1 gap-5 lg:grid-cols-2 lg:items-start">
          <SkillColumn kind="not_evidenced" skills={result.not_evidenced} postingCount={postingCount} />
          <SkillColumn kind="evidenced" skills={result.evidenced} postingCount={postingCount} />
        </div>
      );
    } else if (gap.status === "error") {
      // A failed switch: the selector above still works
      columns = (
        <ProfileLoadError status={gap.httpStatus} message={failureMessage(gap.httpStatus, gap.message)} onRetry={retryGap} />
      );
    } else {
      columns = (
        <div aria-busy="true">
          <SkillGapSkeleton columnsOnly />
        </div>
      );
    }

    return (
      <>
        <p className="mt-6 flex items-start gap-2 text-sm leading-relaxed text-muted-foreground">
          <Info aria-hidden="true" className="mt-0.5 size-4 shrink-0" />
          {MATCHING_NOTE}
        </p>
        <div className="mt-6">{columns}</div>
      </>
    );
  }

  return (
    <div className="max-w-5xl">
      <h1 className="text-2xl font-semibold text-balance">Skill Gap</h1>
      <p className="mt-2 text-base leading-relaxed text-muted-foreground">
        See which skills for your target role are evidenced in your resume, ordered by how often job postings ask
        for them.
      </p>
      <p role="status" className="sr-only">
        {announcement}
      </p>
      <div className="mt-6">{renderContent()}</div>
    </div>
  );
}
