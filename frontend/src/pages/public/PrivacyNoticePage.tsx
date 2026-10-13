import type { ReactNode } from "react";
import { Link } from "react-router";
import { usePageTitle } from "@/hooks/usePageTitle";

// Replace before release
const CONTACT_EMAIL = "[CONTACT EMAIL]";

const LAST_UPDATED_ISO = "2026-10-13";
const LAST_UPDATED = new Intl.DateTimeFormat("en-MY", { dateStyle: "long" }).format(
  new Date(LAST_UPDATED_ISO),
);

const focusRing =
  "rounded-lg focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-600";
const listClass = "list-disc space-y-2 pl-5 marker:text-zinc-400";
const linkClass = `text-emerald-700 underline underline-offset-2 hover:text-emerald-800 ${focusRing}`;

type NoticeSectionProps = { id: string; title: string; children: ReactNode };

function NoticeSection({ id, title, children }: NoticeSectionProps) {
  return (
    <section aria-labelledby={id} className="border-t border-zinc-200 pt-8">
      <h2 id={id} className="scroll-mt-24 text-xl font-semibold text-balance">
        {title}
      </h2>
      <div className="mt-3 space-y-3 text-base leading-relaxed text-zinc-700">{children}</div>
    </section>
  );
}

export default function PrivacyNoticePage() {
  usePageTitle("Privacy Notice | KerjaReady");

  return (
    <div className="min-h-[100dvh] bg-zinc-50 text-zinc-900">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:rounded-lg focus:border focus:border-zinc-500 focus:bg-white focus:px-3 focus:py-2 focus:text-sm"
      >
        Skip to Content
      </a>

      <header className="border-b border-zinc-200">
        <div className="mx-auto flex max-w-3xl items-center justify-between gap-4 px-4 py-4 md:px-8">
          <Link to="/" className={`text-lg font-semibold ${focusRing}`}>
            KerjaReady
          </Link>
          <Link to="/" className={`text-sm text-zinc-600 hover:text-zinc-900 ${focusRing}`}>
            Back to Home
          </Link>
        </div>
      </header>

      <main id="main" className="mx-auto max-w-3xl px-4 py-12 md:px-8 md:py-16">
        <h1 className="text-3xl font-semibold tracking-tight text-balance">Privacy Notice</h1>
        <p className="mt-2 text-sm text-zinc-600">
          Last updated: <time dateTime={LAST_UPDATED_ISO}>{LAST_UPDATED}</time>
        </p>
        <p className="mt-6 max-w-[65ch] text-base leading-relaxed text-zinc-700">
          This notice explains what personal data KerjaReady collects, how it is used and who can
          see it. Please read it before you create an account or upload a resume.
        </p>

        <div className="mt-10 max-w-[65ch] space-y-10">
          <NoticeSection id="about" title="About KerjaReady">
            <p>
              KerjaReady is a prototype career readiness platform for technology students and
              recruiters in Malaysia. It is developed for academic purposes.
            </p>
          </NoticeSection>

          <NoticeSection id="collect" title="What We Collect">
            <ul className={listClass}>
              <li>
                <strong className="font-medium text-zinc-900">Account details:</strong> your name,
                email address and account type. Recruiters also provide a company name.
              </li>
              <li>
                <strong className="font-medium text-zinc-900">Password:</strong> handled by Amazon
                Cognito, our sign-in service. KerjaReady never sees or stores it.
              </li>
              <li>
                <strong className="font-medium text-zinc-900">Resumes:</strong> the files you upload
                and the text taken from them.
              </li>
              <li>
                <strong className="font-medium text-zinc-900">Results:</strong> assessments, the
                skills evidenced in your resume with the text that shows them, recommendations,
                roadmaps and match scores.
              </li>
              <li>
                <strong className="font-medium text-zinc-900">Applications:</strong> the listings you
                apply to, their status and any reason a recruiter gives for a decision.
              </li>
              <li>
                <strong className="font-medium text-zinc-900">Job listings:</strong> the listings
                recruiters post.
              </li>
            </ul>
            <p>
              Do not include details a job application does not need, such as your MyKad number,
              in your resume.
            </p>
          </NoticeSection>

          <NoticeSection id="use" title="How We Use Your Data">
            <ul className={listClass}>
              <li>To assess your resume against the role you choose.</li>
              <li>To show which skills required by that role are evidenced in your resume.</li>
              <li>To generate resume recommendations and a learning roadmap.</li>
              <li>To calculate match scores between your resume and job listings.</li>
              <li>To let you apply to listings and see the outcome.</li>
            </ul>
            <p>
              Some features use AI. Your resume text is processed by Amazon Bedrock to generate
              recommendations and roadmaps. Your resume is not used to train KerjaReady&#39;s
              assessment model, and Amazon Bedrock does not use it to train its models.
            </p>
            <p>We do not sell your data or use it for advertising.</p>
          </NoticeSection>

          <NoticeSection id="access" title="Who Can See Your Data">
            <ul className={listClass}>
              <li>You can see all of your own data.</li>
              <li>
                A recruiter can see your resume, match score and skill evidence only after you apply
                to one of their listings, and only for that listing.
              </li>
              <li>Recruiters see only the applications made to their own listings.</li>
              <li>
                Amazon Web Services (AWS) hosts and processes the data on our behalf. It does not use
                the data for its own purposes.
              </li>
            </ul>
          </NoticeSection>

          <NoticeSection id="storage" title="Where Your Data Is Stored">
            <ul className={listClass}>
              <li>Your data is stored on AWS in the Asia Pacific (Malaysia) region.</li>
              <li>Some AI processing may take place in AWS regions outside Malaysia.</li>
              <li>Stored files and records are encrypted, and all connections use HTTPS.</li>
              <li>You must sign in to reach your data, and each account can reach only its own.</li>
            </ul>
          </NoticeSection>

          <NoticeSection id="retention" title="How Long We Keep Your Data">
            <p>
              We keep your data while your account is active. You can ask us to delete your account
              at any time. All data will be deleted when the KerjaReady prototype is taken offline.
            </p>
          </NoticeSection>

          <NoticeSection id="rights" title="Your Choices and Rights">
            <p>You can ask us to:</p>
            <ul className={listClass}>
              <li>Give you a copy of your personal data.</li>
              <li>Correct personal data that is wrong.</li>
              <li>Delete your account, resumes and results.</li>
              <li>
                Stop processing your data. Withdrawing consent means we can no longer provide the
                service, so your account will be deleted.
              </li>
            </ul>
          </NoticeSection>

          <NoticeSection id="results" title="About Your Results">
            <p>
              Assessments, skill gap analyses and match scores are produced automatically from the
              text of your resume. They show what your resume evidences, not your actual ability. A
              skill marked “not evidenced in the resume” may still be a skill you have.
            </p>
            <p>
              Recruiters make their own decisions. KerjaReady does not accept or reject
              applications.
            </p>
          </NoticeSection>

          <NoticeSection id="contact" title="Contact Us">
            <p>
              For questions about this notice or your data, email{" "}
              <a href={`mailto:${CONTACT_EMAIL}`} className={linkClass}>
                {CONTACT_EMAIL}
              </a>
              . If we change this notice, we will update the date at the top of this page.
            </p>
          </NoticeSection>
        </div>
      </main>
    </div>
  );
}