import { cn } from "cn";
import { letterTile } from "@/lib/roadmapText";

type LetterTileProps = {
  skill: string;
  // The selected skill's tile is dark, the others emerald
  selected?: boolean;
};

// A 44px tile with a skill's letters, such as "TF" for TensorFlow. Decorative: the skill name is always beside it.
export default function LetterTile({ skill, selected = false }: LetterTileProps) {
  return (
    <span
      aria-hidden="true"
      className={cn(
        "flex size-11 shrink-0 items-center justify-center rounded-lg text-sm font-semibold",
        selected ? "bg-zinc-700 text-white" : "bg-primary-subtle text-primary",
      )}
    >
      {letterTile(skill)}
    </span>
  );
}
