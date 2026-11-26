import { useState } from "react";
import { cn } from "cn";
import { letterTile } from "@/lib/roadmapText";
import { skillLogoUrl } from "@/lib/skillLogos";

type SkillTileProps = {
  skill: string;
  // The selected skill's letter tile is dark, the others emerald
  selected?: boolean;
};

const tile = "flex size-11 shrink-0 items-center justify-center rounded-lg";

// A 44px tile beside a skill's name: its official logo, or its letters (such as "ML" for Machine learning) when it
// has none or the logo fails to load. Decorative: the skill name is always beside it. A logo tile stays white when
// selected so dark logos stay visible; the card's border and button label still show the selection.
export default function SkillTile({ skill, selected = false }: SkillTileProps) {
  const logo = skillLogoUrl(skill);
  const [failedLogo, setFailedLogo] = useState<string | null>(null);

  if (logo && failedLogo !== logo) {
    return (
      <span aria-hidden="true" className={cn(tile, "border bg-card")}>
        {/* draggable: a native image drag would stop the carousel's mouse drag */}
        <img
          src={logo}
          alt=""
          width={32}
          height={28}
          decoding="async"
          draggable={false}
          className="h-7 w-8 object-contain"
          onError={() => setFailedLogo(logo)}
        />
      </span>
    );
  }

  return (
    <span
      aria-hidden="true"
      className={cn(
        tile,
        "text-sm font-semibold",
        selected ? "bg-zinc-700 text-white" : "bg-primary-subtle text-primary",
      )}
    >
      {letterTile(skill)}
    </span>
  );
}
