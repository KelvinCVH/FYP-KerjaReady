"""Rubric v1.0 as candidates see it (frontend/src/lib/rubric.ts), shared by the guidance agent's tools (KR-97) and
the roadmap API (KR-98).

Each criterion is (ratings column, name, question, level labels, next-level wording). Levels run 0 to 3; the
next-level wording for a level says what reaching the next one needs, and is None at the top level.
"""

RUBRIC = [
    ("a1_rating", "Work Evidence", "Do the entries say what was built or done, and with which technologies?",
     ["Not shown", "Limited", "Clear", "Strong"],
     ["At least one job, internship or project that says what you built or did and which technologies you used.",
      "More than half of your entries name the specific thing you built or did (a system, feature, report or "
      "script) and the tools you used.",
      "A link to the work itself in at least one entry: a code repository, live demo or portfolio site. A GitHub "
      "profile link alone doesn't count.",
      None]),
    ("a2_rating", "Outcome", "Does the resume say what the work achieved?",
     ["Not shown", "Limited", "Clear", "Strong"],
     ["At least one entry that says what the work achieved: something became faster, more accurate or automated, "
      "or users or a client adopted it.",
      "A concrete result in more than half of your entries. \"Built a dashboard\" is a task; \"The sales team now "
      "uses the dashboard for weekly reviews\" is a result.",
      "At least one result measured with a number, such as \"cut the report time from 6 hours to 2\". Team size or "
      "the number of reports doesn't count.",
      None]),
    ("a3_rating", "Skill in Use", "Are skills shown being used, not just listed?",
     ["Not shown", "Limited", "Clear", "Strong"],
     ["Tools mentioned inside your entry descriptions, not only in the skills list.",
      "More than half of your entries say what a tool was used for, such as \"Used Python to automate the monthly "
      "report\".",
      "Nearly all entries give each tool its own job: \"Built the interface with React and the API with Spring "
      "Boot\", not \"using Java, Spring and Hibernate\".",
      None]),
    ("b2_rating", "Language Quality", "Is the writing free of spelling and grammar errors?",
     ["Hard to read", "Several errors", "Minor errors", "No errors found"],
     [None,
      "No more than two spelling, grammar or product-name errors. The Resume page lists the errors found.",
      "No spelling, grammar or product-name errors. The Resume page lists the errors found.",
      None]),
]