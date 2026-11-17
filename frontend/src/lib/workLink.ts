const WEB_LINK = /^https?:\/\//i;

// A work link found in the resume. It comes from the resume's own text, so only http and https
// addresses become links; anything else (such as "javascript:") is shown as plain text.
export function toWorkLink(raw: string): { display: string; href: string | null } {
  const value = raw.trim();
  const isWebLink = WEB_LINK.test(value);
  return { display: value.replace(WEB_LINK, ""), href: isWebLink ? value : null };
}
