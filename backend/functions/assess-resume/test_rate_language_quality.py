"""Tests for the B2 error counting, with LanguageTool responses written by hand (no server needed).
Run: python -m pytest inference
"""

from rate_language_quality import count_errors, level_from_count


def match(text, word, rule="MORFOLOGIK_RULE_EN_GB", category="TYPOS", issue="misspelling", replacements=(), nth=0):
    start = -1
    for _ in range(nth + 1):
        start = text.index(word, start + 1)
    return {"offset": start, "length": len(word), "message": "msg",
            "replacements": [{"value": r} for r in replacements],
            "rule": {"id": rule, "issueType": issue, "category": {"id": category}}}


def test_spelling_counts_only_when_both_variants_flag_it():
    # "organised" is British spelling: only en-US flags it, so it is not an error
    text = "developped reports and organised the team."
    gb = [match(text, "developped")]
    us = [match(text, "developped", rule="MORFOLOGIK_RULE_EN_US"), match(text, "organised", rule="MORFOLOGIK_RULE_EN_US")]
    assert [e["text"] for e in count_errors(text, gb, us)] == ["developped"]


def test_capitalised_words_and_run_together_words_are_ignored():
    text = "Used Kubernetes and Sagemaker; tested usingautomated tools."
    gb = [match(text, "Kubernetes"), match(text, "Sagemaker"),
          match(text, "usingautomated", replacements=["using automated"])]
    assert count_errors(text, gb, gb) == []


def test_grammar_counts_and_style_and_spacing_do_not():
    text = "He have built it. Hands - on with a very unique tool ."
    gb = [match(text, "have", rule="HE_VERB_AGR", category="GRAMMAR", issue="grammar"),
          match(text, " - ", rule="WHITESPACE_RULE", category="TYPOGRAPHY", issue="whitespace"),
          match(text, "very unique", rule="VERY_UNIQUE", category="STYLE", issue="style"),
          match(text, " .", rule="COMMA_PARENTHESIS_WHITESPACE", category="TYPOGRAPHY", issue="whitespace")]
    assert [e["rule"] for e in count_errors(text, gb, [])] == ["HE_VERB_AGR"]


def test_style_rules_seen_on_real_resumes_are_ignored():
    text = "Subject Matter Experts, day to day, stand alone apps, problem solving, node js, Base line"
    gb = [match(text, "Subject Matter Experts", rule="SUBJECT_MATTER_HYPHEN", category="TYPOS", issue="misspelling"),
          match(text, "day to day", rule="DAY_TO_DAY_HYPHEN", category="TYPOS", issue="misspelling"),
          match(text, "stand alone", rule="STAND_ALONE_NN", category="TYPOS", issue="misspelling"),
          match(text, "problem solving", rule="PROBLEM_SOLVE_HYPHEN", category="TYPOS", issue="misspelling"),
          match(text, "js", rule="FILE_EXTENSIONS_CASE", category="CASING", issue="typographical"),
          match(text, "Base line", rule="LINE_COMPOUNDS", category="TYPOS", issue="misspelling")]
    assert count_errors(text, gb, gb) == []


def test_it_acronym_preposition_and_hyphen_messages_are_ignored():
    text = "IT Support for pre and post session tasks in windows"
    hyphen = match(text, "pre and post session", rule="PRE_AND_POST_NN", category="GRAMMAR", issue="grammar")
    hyphen["message"] = "It appears that hyphens are missing."
    gb = [match(text, "Support", rule="IT_VBZ", category="GRAMMAR", issue="grammar"), hyphen,
          match(text, "in", rule="IN_WINDOWS", category="GRAMMAR", issue="grammar"),
          match(text, "windows", rule="A_WINDOWS", category="CASING", issue="typographical")]
    assert [e["rule"] for e in count_errors(text, gb, gb)] == ["A_WINDOWS"]


def test_product_name_and_grammar_rules_still_count():
    text = "Used Power Point and Java script for create slides."
    gb = [match(text, "Power Point", rule="MICROSOFT_PRODUCTS", category="TYPOS", issue="misspelling"),
          match(text, "Java script", rule="JAVA_SCRIPT", category="TYPOS", issue="misspelling"),
          match(text, "for create", rule="FOR_VB", category="GRAMMAR", issue="grammar")]
    assert len(count_errors(text, gb, gb)) == 3


def test_joined_words_and_inner_capitals_are_ignored_but_real_misspellings_count():
    text = "worked withiterationand iBatis, abbends, responsibilites"
    gb = [match(text, w) for w in ["withiterationand", "iBatis", "abbends", "responsibilites"]]
    assert [e["text"] for e in count_errors(text, gb, gb)] == ["abbends", "responsibilites"]


def test_repeated_mistake_counts_once_and_sentence_start_rule_is_ignored():
    text = "managment of tools. managment of staff. reporting."
    gb = [match(text, "managment"), match(text, "managment", nth=1),
          match(text, "reporting", rule="UPPERCASE_SENTENCE_START", category="CASING", issue="typographical")]
    assert len(count_errors(text, gb, gb)) == 1


def test_levels():
    assert [level_from_count(n) for n in (0, 1, 2, 3, 10)] == [3, 2, 2, 1, 1]