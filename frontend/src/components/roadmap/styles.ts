// Shared class strings for the Learning Roadmap

// A skill card's width in the carousel: 3 across on a wide page, at least 260px, so a phone shows 1 and the next
// peeks in. Shared with the skeleton so it has the same shape.
export const skillCardWidth = "w-[max(260px,calc((100%_-_2rem)/3))]";

// A heading that gets focus from code (tabIndex -1) when the content above it changes, on a white card
export const focusedHeading =
  "rounded-md outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-card";

// A sub-section heading inside a roadmap card or the details panel
export const minorHeading = "text-sm font-semibold";
