// Separates the email form from Continue with Google
export default function OrDivider() {
  return (
    <div className="flex items-center gap-3 text-sm text-muted-foreground">
      <span aria-hidden="true" className="h-px flex-1 bg-border" />
      or
      <span aria-hidden="true" className="h-px flex-1 bg-border" />
    </div>
  );
}
