import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "cn"
import { Slot } from "radix-ui"

// Colours follow DESIGN.md Section 5.2. Pair every badge with an icon and a text label.
const badgeVariants = cva(
  "inline-flex w-fit shrink-0 items-center gap-1.5 whitespace-nowrap rounded-lg px-2 py-0.5 text-sm font-medium [&>svg]:pointer-events-none [&>svg]:size-4 [&>svg]:shrink-0",
  {
    variants: {
      variant: {
        success: "bg-emerald-50 text-emerald-800",
        neutral: "bg-zinc-100 text-zinc-700",
        rejected: "bg-zinc-200 text-zinc-800",
        warning: "bg-amber-50 text-amber-800",
        error: "bg-red-50 text-red-700",
        // Still running: white with a border, so it keeps its shape on a zinc-100 row. The icon spins.
        progress: "border bg-card text-zinc-700 [&>svg]:motion-safe:animate-spin",
      },
    },
    defaultVariants: {
      variant: "neutral",
    },
  }
)

function Badge({
  className,
  variant = "neutral",
  asChild = false,
  ...props
}: React.ComponentProps<"span"> &
  VariantProps<typeof badgeVariants> & { asChild?: boolean }) {
  const Comp = asChild ? Slot.Root : "span"

  return (
    <Comp
      data-slot="badge"
      data-variant={variant}
      className={cn(badgeVariants({ variant }), className)}
      {...props}
    />
  )
}

export { Badge, badgeVariants }
