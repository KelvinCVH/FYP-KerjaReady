// Shared class strings for the auth pages

const focusRing =
  "rounded-md outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-card";

// Emerald underlined link inside body text, such as "Sign In" or "Privacy Notice"
export const inlineLink = `text-primary underline underline-offset-2 hover:text-primary-hover ${focusRing}`;

// Standalone emerald link with no underline until hover, such as "Forgot Password?"
export const accentLink = `text-sm font-medium text-primary underline-offset-2 transition-colors duration-150 hover:text-primary-hover hover:underline ${focusRing}`;

// Underlined link inside red error text
export const errorLink = `font-medium text-current underline underline-offset-2 ${focusRing}`;

// Quiet text link or link-styled button, such as "Change Account Type"
export const quietLink = `text-sm text-muted-foreground transition-colors duration-150 hover:text-foreground ${focusRing}`;

// 48px emerald-50 tile holding a page icon (Check Your Email, Your Account Is Ready)
export const iconTile =
  "flex size-12 items-center justify-center rounded-xl bg-primary-subtle text-primary [&_svg]:size-6";
