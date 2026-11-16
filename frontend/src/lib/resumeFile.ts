// The largest resume S3 accepts, matching the backend's upload policy
export const MAX_RESUME_BYTES = 5 * 1024 * 1024;

// Keeps a number and its unit on one line, such as "5 MB"
const NBSP = String.fromCharCode(160);

const sizeFormat = new Intl.NumberFormat("en-MY", { maximumFractionDigits: 1 });

// The message to show when a file can't be uploaded as a resume, or null when it can.
// An empty type is allowed because some systems don't report one for PDFs. S3 checks the form's
// Content-Type field rather than the file, and the server checks the real PDF later.
export function validateResumeFile(file: File) {
  const isPdf = file.name.toLowerCase().endsWith(".pdf") && (file.type === "application/pdf" || file.type === "");
  if (!isPdf) return "This file isn’t a PDF. Choose a PDF file.";
  if (file.size > MAX_RESUME_BYTES) return `This PDF is over 5${NBSP}MB. Choose a smaller file.`;
  if (file.size === 0) return "This PDF is empty. Choose another file.";
  return null;
}

// A file size such as "248 KB" or "1.2 MB". Intl's unit style would print "kB".
export function formatFileSize(bytes: number) {
  if (bytes < 1024 * 1024) return `${sizeFormat.format(Math.max(1, Math.round(bytes / 1024)))}${NBSP}KB`;
  return `${sizeFormat.format(bytes / (1024 * 1024))}${NBSP}MB`;
}
