const dateFormat = new Intl.DateTimeFormat("en-MY", { day: "numeric", month: "short", year: "numeric" });

// An ISO 8601 timestamp as a date in the browser's time zone, such as "17 Nov 2026"
export function formatDate(iso: string) {
  return dateFormat.format(new Date(iso));
}
