# KerjaReady Resume Labelling Guide v1.4 (Rubric v1.0)

Used for both manual labelling and the LLM labelling prompt. Change it only between labelling rounds, and record the version.

v1.1 (30 Oct 2026) adds eight clarifications found while labelling the 30 calibration resumes. They are marked [v1.1].

v1.2 (30 Oct 2026) fixes six ambiguities found when comparing LLM labels with the calibration labels. They are marked [v1.2]. No calibration label changed.

v1.3 (30 Oct 2026) widens the v1.2 definition of a specific piece of work to include documents and queries, and states two rules that were implied. They are marked [v1.3]. No calibration label changed.

v1.4 (30 Oct 2026) fixes the scope rule and the A3 level 0 rule after a check of the first 1,000 LLM labels. They are marked [v1.4]. No calibration label changed.

## 1. Task

Rate how clearly the resume presents evidence of technical work, on four criteria: A1, A2, A3 and B2. Each is rated 0 to 3.

- Rate only what is written. Do not guess what the candidate meant.
- Do not judge the candidate's ability, seniority, years of experience or fit for any role.
- Rate the whole resume, and rate each criterion on its own.
- Ignore CGPA or GPA, university, certifications and photos.
- B1 (organisation) is not rated here, because this text has no layout.

## 2. Out of scope

Mark the resume **out of scope** and leave the ratings blank if no entry describes work on software, data, networks or IT systems. Examples: finance, accounting, sales, recruiting or general administration only.

A business analyst resume is in scope if at least one entry describes work on an IT system or data (for example, writing requirements for software, testing, SQL queries or reports).

[v1.4] Scope depends only on whether at least one entry describes such work, not on what most of the resume is about. One IT entry among many sales or manufacturing jobs is enough. Installing or repairing computers, network hardware or network cabling counts as work on IT systems or networks.

[v1.4] A resume with no entries (only a summary, skills and education) is in scope if its summary or skills are about IT work. Rate it: A1, A2 and A3 are 0.

## 3. Key terms

**Entry.** A job, internship, project or activity with its own description.
- The summary, skills list, education and certifications are not entries.
- Each job counts as one entry, even if it lists several projects inside it. A project counts as a separate entry only when it sits in its own Projects section with its own description.
- The same work described in two places counts as one entry. [v1.1] Two jobs whose descriptions are identical or nearly identical also count as one entry.
- A job with only a title, company and dates, and no description, is still an entry. It counts as "named only".

**Counting entries.**

| Entries | More than half | Half or fewer | Nearly all |
|---|---|---|---|
| 1 | 1 | 0 | 1 |
| 2 | 2 | 0 to 1 | 2 |
| 3 | 2 or more | 0 to 1 | 3 |
| 4 | 3 or more | 0 to 2 | 4 |
| 5 | 3 or more | 0 to 2 | 4 or more |
| 6 | 4 or more | 0 to 3 | 5 or more |
| 7 | 4 or more | 0 to 3 | 6 or more |
| 8 | 5 or more | 0 to 4 | 7 or more |
| n | more than n/2 | n/2 or fewer | all, or all but one when n is 5 or more |

[v1.3] Exactly half is not more than half: 3 of 6 and 4 of 8 are "half or fewer".

**Listed vs shown in use.** A skill is shown in use when a sentence in an entry says what it was used for ("Used Log4J to capture application logs"). A skill named only in the summary, the skills list, or an "Environment:", "Technologies:" or "Tools:" line is listed, not shown in use.

**Concrete result.** What the work achieved or changed: something became faster, cheaper, more accurate or automated; users or a client adopted or approved it; it won an award. These are not results:
- a task ("Developed stored procedures")
- a feature ("The report shows daily sales by region")
- a purpose or intention ("to improve performance", "in order to reduce errors")
- a finished deliverable ("Built a dashboard"), which counts as work under A1
- a vague contribution ("Helped improve the system", "Ensured quality"), which is only a hint of a result
- [v1.1] self-praise about a task ("Successfully performed testing", "in an effective way"), which is not even a hint
- [v1.1] the size or completion of a task ("Archived 9000+ assets", "Executed 100% of the test cases", "Developed dozens of batch jobs")

[v1.2] Upgrading, migrating, installing or setting up something is a task, not a result, unless the resume says what improved because of it ("Upgraded the cluster from CDH3 to CDH4" is a task).

[v1.1] Wording decides between a result and a purpose. "Automated the nightly load" and "Improved query performance by adding indexes" state what was achieved, so they are concrete results (not measured). "Wrote scripts to automate the nightly load" and "Added indexes to improve performance" state an intention, so they are purposes.

**Measured result.** A concrete result with a number that measures what the work achieved ("Reduced nightly load time from 6 hours to 2", "Cut defects by 30%"). Numbers about effort or size do not count: team size, number of users supported, database size, number of reports, years of experience, number of commits.

**[v1.1] Named skill.** A specific tool, language, platform or product ("Active Directory", "Informatica", "Cisco routers"). General areas such as "LAN/WAN technologies", "server technologies" or "various tools" are not named skills, for A1 or A3. [v1.2] Nor are kinds of system or software ("billing system", "CRM", "OSS", "provisioning systems", "appraisal software") unless a product is named ("Salesforce CRM").

[v1.2] Parts of a tool are not separate skills. Components and features of a tool (Informatica transformations such as Joiner or Lookup, Source Analyzer, Workflow Manager) belong to that tool.

**[v1.1] Support and administration work.** Installing, configuring, administering or troubleshooting a named technology counts as showing it in use ("Configured Cisco and Juniper routers", "Added users to Exchange via Active Directory").

**Own job vs shared job (A3 level 3).**
- Own job: the sentence says what that particular tool did ("Built the UI with Angular and the REST API with Spring Boot").
- Shared job: several tools are named for one task ("Developed the application using Java, Spring and Hibernate"). This counts as shown in use for level 2, but not as each tool having its own job for level 3.
- [v1.2] One tool used for several purposes is not a shared job ("Developed Ab Initio graphs for data cleansing, validation and transformation" gives Ab Initio its own job).

## 4. Criteria

### A1 Work Evidence: Does each entry say what was built or done, and with which technologies?

| Level | Meaning |
|---|---|
| 0 | No entry is described. The resume has only skills, education or a list of courses. |
| 1 | Entries are only named or described in general terms. Half or fewer of the entries say what was built or done and which technologies were used. |
| 2 | More than half of the entries say what was built or done and which named technologies were used. |
| 3 | Level 2, plus at least one entry links to the work itself: a code repository, live demo or personal portfolio site. A GitHub profile link alone does not count. [v1.1] A website the candidate says they built or designed counts as a link to the work. [v1.2] This includes an employer's or client's site when the link is given with that claim ("Website design and maintenance: www.example.com"). A URL that only identifies the employer does not count. |

For A1, technologies on an "Environment:" line do count as saying which technologies were used. A3 is stricter.

[v1.2] "What was built or done" means a specific piece of work: a system, module, feature, report, script, interface, migration or configuration ("Developed the claims intake module", "Configured VLANs for the branch network"). [v1.3] Documents, diagrams, test plans, test cases and queries also count ("Created use case diagrams in MS Visio", "Wrote SQL queries to validate the loaded data"). General activities are "general terms", even with an Environment line: "Coding Java programming", "Analysis of the requirements and design", "Writing unit test cases", "Involved in all phases of SDLC".

[v1.1] Work done for an employer or internship is often confidential and cannot be linked. One link in any entry, such as a personal or university project, is enough for level 3.

### A2 Outcome: Does the resume say what the work achieved?

| Level | Meaning |
|---|---|
| 0 | No entry states a result or hints at one. Entries give only tasks, features, purposes, sizes or self-praise. |
| 1 | [v1.2] At least one entry hints at a result (a vague contribution such as "Ensured quality" or "Helped improve the system") or states a concrete result, but half or fewer of the entries state a concrete result. |
| 2 | More than half of the entries state a concrete result. |
| 3 | Level 2, plus at least one result is measured with a number. |

Level 3 needs level 2 first. A measured result in only one of five entries is level 1.

[v1.2] The 0 or 1 decision: a purpose ("to improve performance") gives nothing, a vague contribution gives a hint, so one vague contribution anywhere is enough for level 1.

### A3 Skill in Use: Are skills shown being used in entries, not just listed?

| Level | Meaning |
|---|---|
| 0 | Skills appear only in the skills list, the summary or "Environment:" lines. No sentence in an entry names a skill. [v1.4] A skill named in an entry sentence, even without saying what it did ("Experience with QuickBooks"), gives at least level 1. |
| 1 | Some entries name skills in a sentence, but half or fewer show what a skill was used for. |
| 2 | More than half of the entries show what at least one named skill was used for. |
| 3 | Nearly all entries name skills and give every named skill its own job. |

For level 3, an entry does not count if it names a tool (in a sentence or on its "Environment:" line) that no sentence in that entry explains. Tools on the "Environment:" line that are explained in the entry's sentences are fine. The length of the skills list has no effect.

### B2 Language Quality: Is the writing correct and consistent?

| Level | Meaning |
|---|---|
| 0 | Errors are so frequent that the resume is hard to read. |
| 1 | Errors appear in three or more places, or the tense is inconsistent. |
| 2 | One or two small errors, and the tense is consistent. |
| 3 | No errors, and the tense is consistent. |

- Errors are spelling, grammar, punctuation that changes the meaning, and misspelled or wrongly capitalised product names ("Postgress", "Javscript", "Sagemaker", "Javascript").
- [v1.3] B2 covers the whole resume, including the summary and skills list.
- Count distinct errors. The same mistake repeated counts once.
- Not errors: British, American or Malaysian spelling; product names written entirely in capitals ("JAVA", "MYSQL"), which is a style choice; the "Confidential" placeholder; missing spaces, run-together words or stray characters caused by text extraction. [v1.2] Spaces around hyphens and slashes ("Hands - on", "Multi - Tier", "report / data", "11.0 / / UFT") are also extraction artefacts.
- Tense is inconsistent when one entry mixes past and present verbs ("Developed... Creates..."), or when a past role uses the present tense ("Develops reports"). The current role may use the present tense. An entry written consistently in the "-ing" form ("Designing and developing...") is not inconsistent.

## 5. Notes for this corpus

- The text has no line breaks. Section headings ("PROFESSIONAL EXPERIENCE", "Responsibilities:", "Environment:") appear inline. Use job titles, company names and dates to find where each entry starts.
- "Confidential" replaces company and client names. Ignore it.
- Many resumes have many jobs. Count every job as an entry before applying "more than half" or "nearly all".
- Links are almost never present, so A1 is rarely 3.