import { cn } from "cn"

// zinc-100 placeholder with the 8px control radius (DESIGN.md 5.1, 9.3). Shape it like the content it stands in for.
function Skeleton({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="skeleton"
      className={cn("animate-pulse rounded-md bg-muted", className)}
      {...props}
    />
  )
}

export { Skeleton }
