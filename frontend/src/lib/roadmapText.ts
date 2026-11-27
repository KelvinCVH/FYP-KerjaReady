// Small text helpers for the Learning Roadmap. Everything here returns plain strings: the roadmap is written by AI,
// so it is only ever rendered as text, never as HTML or markdown.

export type TextPart = { text: string; placeholder: boolean };

const PLACEHOLDER = /\[[^\]\n]+\]/g;

// "Trained a [model type] with [framework]" → the plain runs and the [placeholders], in order, brackets kept
export function splitPlaceholders(text: string): TextPart[] {
  const parts: TextPart[] = [];
  let last = 0;
  for (const match of text.matchAll(PLACEHOLDER)) {
    const start = match.index ?? 0;
    if (start > last) parts.push({ text: text.slice(last, start), placeholder: false });
    parts.push({ text: match[0], placeholder: true });
    last = start + match[0].length;
  }
  if (last < text.length) parts.push({ text: text.slice(last), placeholder: false });
  return parts;
}

// The letters on a skill's tile: the skill itself when it is 3 characters or fewer ("C#"), its first two capitals
// ("TensorFlow" → "TF", "Microsoft Azure" → "MA"), or the first letters of its first two words ("Computer vision" →
// "CV"). A single word with one capital gives its first two letters ("Python" → "Py").
export function letterTile(skill: string) {
  const name = skill.trim();
  if (name.length <= 3) return name;
  const capitals = name.match(/[A-Z]/g) ?? [];
  if (capitals.length >= 2) return capitals.slice(0, 2).join("");
  const words = name.split(/\s+/).filter(Boolean);
  if (words.length >= 2) return (words[0][0] + words[1][0]).toUpperCase();
  return name.slice(0, 2);
}

export type SearchLink = { site: string; href: string; label: string };

// Search links for one term on each learning site. The sites show their own results; KerjaReady hasn't checked them.
export function searchLinks(term: string): SearchLink[] {
  const q = encodeURIComponent(term);
  return [
    { site: "YouTube", href: `https://www.youtube.com/results?search_query=${q}&sp=EgIIBQ%3D%3D` },
    { site: "Coursera", href: `https://www.coursera.org/search?query=${q}` },
    { site: "Udemy", href: `https://www.udemy.com/courses/search/?q=${q}` },
  ].map((link) => ({ ...link, label: `Search ${link.site} for ${term} (opens in a new tab)` }));
}

// Share of the role's postings that ask for the skill, as a whole percentage
export function postingPercent(postings: number, rolePostings: number) {
  return rolePostings > 0 ? Math.round((postings / rolePostings) * 100) : 0;
}

// ["A"] → "A", ["A", "B"] → "A and B", ["A", "B", "C"] → "A, B and C"
export function joinNames(names: string[]) {
  if (names.length < 2) return names[0] ?? "";
  return `${names.slice(0, -1).join(", ")} and ${names[names.length - 1]}`;
}

// The reminder above the skills once at least one is done, with the names in roadmap order
export function doneBannerText(names: string[]) {
  const one = names.length === 1;
  return (
    `${joinNames(names)} ${one ? "is" : "are"} done. Include ${one ? "it" : "them"} in your resume now. ` +
    "When you are ready, upload your updated resume to see your new skill gap and learning roadmap."
  );
}
