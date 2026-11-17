// Rubric v1.0 wording shown to candidates on the Resume page.
// The ratings themselves come from GET /candidate/resumes/latest as a1, a2, a3 and b2.
// Show the names below, never the codes. Change wording only with a new rubric version.

export type CriterionKey = "a1" | "a2" | "a3" | "b2";
export type RubricSection = "content" | "presentation";

export type RubricLevel = {
  label: string;
  meaning: string;
  // What the next level needs; null at level 3, and where the checker never gives that level
  nextLevel: string | null;
};

export type RubricCriterion = {
  key: CriterionKey;
  name: string;
  question: string;
  section: RubricSection;
  levels: [RubricLevel, RubricLevel, RubricLevel, RubricLevel];
};

export const RUBRIC_SECTIONS: { key: RubricSection; title: string }[] = [
  { key: "content", title: "Content" },
  { key: "presentation", title: "Presentation" },
];

export const RUBRIC: RubricCriterion[] = [
  {
    key: "a1",
    name: "Work Evidence",
    question: "Do your entries say what you built or did, and with which technologies?",
    section: "content",
    levels: [
      {
        label: "Not shown",
        meaning: "No job, internship or project is described. The resume lists only skills, education or courses.",
        nextLevel: "At least one job, internship or project that says what you built or did and which technologies you used.",
      },
      {
        label: "Limited",
        meaning: "Entries are named or described in general terms. Half or fewer say what you built or did and with which technologies.",
        nextLevel:
          "More than half of your entries name the specific thing you built or did (a system, feature, report or script) and the tools you used.",
      },
      {
        label: "Clear",
        meaning: "More than half of your entries say what you built or did and which technologies you used.",
        nextLevel:
          "A link to the work itself in at least one entry: a code repository, live demo or portfolio site. A GitHub profile link alone doesn’t count.",
      },
      {
        label: "Strong",
        meaning: "Most entries describe specific work and technologies, and at least one links to the work itself.",
        nextLevel: null,
      },
    ],
  },
  {
    key: "a2",
    name: "Outcome",
    question: "Does your resume say what your work achieved?",
    section: "content",
    levels: [
      {
        label: "Not shown",
        meaning: "Entries list tasks, features or goals, but none says what the work achieved.",
        nextLevel:
          "At least one entry that says what the work achieved: something became faster, more accurate or automated, or users or a client adopted it.",
      },
      {
        label: "Limited",
        meaning: "At least one entry hints at or states a result, but half or fewer state a concrete result.",
        nextLevel:
          "A concrete result in more than half of your entries. “Built a dashboard” is a task; “The sales team now uses the dashboard for weekly reviews” is a result.",
      },
      {
        label: "Clear",
        meaning: "More than half of your entries state a concrete result.",
        nextLevel:
          "At least one result measured with a number, such as “cut the report time from 6 hours to 2”. Team size or the number of reports doesn’t count.",
      },
      {
        label: "Strong",
        meaning: "More than half of your entries state a concrete result, and at least one is measured with a number.",
        nextLevel: null,
      },
    ],
  },
  {
    key: "a3",
    name: "Skill in Use",
    question: "Are your skills shown being used, not just listed?",
    section: "content",
    levels: [
      {
        label: "Not shown",
        meaning: "Skills appear only in your skills list or summary. No entry mentions a skill in a sentence.",
        nextLevel: "Tools mentioned inside your entry descriptions, not only in the skills list.",
      },
      {
        label: "Limited",
        meaning: "Some entries name skills, but half or fewer show what a skill was used for.",
        nextLevel: "More than half of your entries say what a tool was used for, such as “Used Python to automate the monthly report”.",
      },
      {
        label: "Clear",
        meaning: "More than half of your entries show what at least one named skill was used for.",
        nextLevel:
          "Nearly all entries give each tool its own job: “Built the interface with React and the API with Spring Boot”, not “using Java, Spring and Hibernate”.",
      },
      {
        label: "Strong",
        meaning: "Nearly all entries name skills and say what each one was used for.",
        nextLevel: null,
      },
    ],
  },
  {
    key: "b2",
    name: "Language Quality",
    question: "Is the writing free of spelling and grammar errors?",
    section: "presentation",
    levels: [
      {
        label: "Hard to read",
        meaning: "Errors are so frequent that the resume is hard to read.",
        nextLevel: null, // the checker never gives level 0
      },
      {
        label: "Several errors",
        meaning: "Spelling, grammar or product-name errors appear in three or more places.",
        nextLevel: "No more than two errors. The errors found are listed below.",
      },
      {
        label: "Minor errors",
        meaning: "One or two spelling, grammar or product-name errors were found.",
        nextLevel: "No errors. The errors found are listed below.",
      },
      {
        label: "No errors found",
        meaning: "No spelling, grammar or product-name errors were found.",
        nextLevel: null,
      },
    ],
  },
];