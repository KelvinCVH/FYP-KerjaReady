const dateFormat = new Intl.DateTimeFormat("en-MY", { day: "numeric", month: "short", year: "numeric" });

// A date-only string ("2024-02-01") is read as midnight UTC, so it is formatted in UTC: in a time zone behind UTC
// it would otherwise fall back to the previous day, and on the 1st to the previous month
const monthFormat = new Intl.DateTimeFormat("en-MY", { month: "short", year: "numeric", timeZone: "UTC" });

// An ISO 8601 timestamp as a date in the browser's time zone, such as "17 Nov 2026"
export function formatDate(iso: string) {
  return dateFormat.format(new Date(iso));
}

// A "YYYY-MM-DD" date as its month, such as "Feb 2024"
export function formatMonth(isoDate: string) {
  return monthFormat.format(new Date(isoDate));
}
