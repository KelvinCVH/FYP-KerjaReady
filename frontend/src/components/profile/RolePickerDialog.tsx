import { useRef, useState } from "react";
import { cn } from "cn";
import { Search } from "lucide-react";
import FormAlert from "@/components/auth/FormAlert";
import LoadingButton from "@/components/LoadingButton";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { getApiErrorMessage } from "@/lib/apiClient";
import { saveTargetRole, type Role } from "@/lib/profileApi";
import { sectionIconTile } from "./styles";

type RolePickerDialogProps = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  roles: Role[];
  savedRole: Role | null;
  // Called with the role the API saved; the parent closes the dialog
  onSaved: (role: Role | null) => void;
  // Where focus goes when the dialog closes (the opening button may be gone after a save)
  onCloseAutoFocus: (event: Event) => void;
};

const numberFormat = new Intl.NumberFormat("en-MY");
const pluralRules = new Intl.PluralRules("en-MY");

// "16 roles", "1 role matches “ai”", "3 roles match “data”" or "No roles match “xyz”."
function describeMatches(count: number, search: string) {
  const one = pluralRules.select(count) === "one";
  const roles = `${numberFormat.format(count)} ${one ? "role" : "roles"}`;
  if (!search) return roles;
  if (count === 0) return `No roles match “${search}”.`;
  return `${roles} ${one ? "matches" : "match"} “${search}”`;
}

// Single-choice list of KB roles with a search box. Give it a new key each time it opens, so the search,
// selection and error start fresh.
export default function RolePickerDialog({
  open,
  onOpenChange,
  roles,
  savedRole,
  onSaved,
  onCloseAutoFocus,
}: RolePickerDialogProps) {
  const savedId = savedRole?.role_id ?? null;
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState<number | null>(savedId);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const searchRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const search = query.trim();
  const needle = search.toLocaleLowerCase("en-MY");
  const matches = roles.filter((role) => role.title.toLocaleLowerCase("en-MY").includes(needle));
  const unchanged = selectedId === null || selectedId === savedId;

  // Scroll a saved role that starts out of sight into the middle of the list. Focus then goes to the search.
  function handleOpenAutoFocus() {
    const list = listRef.current;
    const row = list?.querySelector<HTMLElement>("[data-current-role]");
    if (list && row && row.offsetTop >= list.clientHeight) {
      list.scrollTop = row.offsetTop - (list.clientHeight - row.offsetHeight) / 2;
    }
  }

  function preventWhileSaving(event: Event) {
    if (saving) event.preventDefault();
  }

  function clearSearch() {
    setQuery("");
    searchRef.current?.focus();
  }

  async function handleSave() {
    if (unchanged) return;
    setSaving(true);
    setError(null);
    try {
      onSaved(await saveTargetRole(selectedId));
    } catch (saveError) {
      setError(getApiErrorMessage(saveError));
      setSaving(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        closeDisabled={saving}
        onOpenAutoFocus={handleOpenAutoFocus}
        onCloseAutoFocus={onCloseAutoFocus}
        onEscapeKeyDown={preventWhileSaving}
        onInteractOutside={preventWhileSaving}
        // Anchored to the top so the dialog does not jump as the list shrinks
        className="top-16 max-w-130 translate-y-0 gap-0 sm:max-w-130"
      >
        <DialogHeader>
          <DialogTitle>Choose Your Target Role</DialogTitle>
          <DialogDescription>Skill gap analysis and your learning roadmap will be based on this role.</DialogDescription>
        </DialogHeader>

        <div className="mt-6">
          <Label htmlFor="role-search">Search Roles</Label>
          <div className="relative mt-2">
            <Search
              aria-hidden="true"
              className="pointer-events-none absolute top-1/2 left-3 size-5 -translate-y-1/2 text-muted-foreground"
            />
            <Input
              ref={searchRef}
              id="role-search"
              name="role-search"
              type="search"
              autoComplete="off"
              spellCheck={false}
              placeholder="Type a role name…"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              disabled={saving}
              aria-describedby="role-search-count"
              className="pl-10 [&::-webkit-search-cancel-button]:appearance-none"
            />
          </div>
          {/* Announces the count as the user types. With no matches it carries the no-match sentence. */}
          <p
            id="role-search-count"
            aria-live="polite"
            className={cn("mt-2 text-sm text-muted-foreground tabular-nums", matches.length === 0 && "sr-only")}
          >
            {describeMatches(matches.length, search)}
          </p>
        </div>

        {matches.length > 0 ? (
          // Padding keeps the rows' focus rings inside the scroll box; the negative margin cancels it
          <div ref={listRef} className="relative -mx-1 mt-2 max-h-82 overflow-y-auto overscroll-contain p-1">
            <RadioGroup
              aria-label="Roles"
              value={selectedId === null ? "" : String(selectedId)}
              onValueChange={(value) => setSelectedId(Number(value))}
              disabled={saving}
              className="gap-0"
            >
              {matches.map((role) => {
                const id = `role-${role.role_id}`;
                const isCurrent = role.role_id === savedId;
                return (
                  <label
                    key={role.role_id}
                    htmlFor={id}
                    data-current-role={isCurrent || undefined}
                    className="group flex h-12 cursor-pointer items-center gap-3 rounded-lg border border-transparent px-3 transition-[background-color,border-color] duration-150 not-has-[[data-state=checked]]:hover:bg-accent has-[[data-state=checked]]:border-primary has-[[data-state=checked]]:bg-primary-subtle has-focus-visible:ring-2 has-focus-visible:ring-ring has-focus-visible:ring-offset-2 has-focus-visible:ring-offset-card has-[[data-disabled]]:pointer-events-none has-[[data-disabled]]:opacity-50"
                  >
                    <RadioGroupItem
                      id={id}
                      value={String(role.role_id)}
                      aria-labelledby={`${id}-title`}
                      aria-describedby={isCurrent ? `${id}-current` : undefined}
                      className="focus-visible:ring-0 focus-visible:ring-offset-0"
                    />
                    <span id={`${id}-title`} className="min-w-0 flex-1 truncate text-base">
                      {role.title}
                    </span>
                    {isCurrent && (
                      <Badge id={`${id}-current`} className="group-has-[[data-state=checked]]:bg-card">
                        Current
                      </Badge>
                    )}
                  </label>
                );
              })}
            </RadioGroup>
          </div>
        ) : (
          <div className="flex flex-col items-center pt-10 pb-2 text-center">
            <div className={`${sectionIconTile} bg-muted text-foreground`}>
              <Search aria-hidden="true" />
            </div>
            <h3 className="mt-3 max-w-full text-base font-semibold break-words">No roles match “{search}”.</h3>
            <p className="mt-2 text-sm text-muted-foreground">Check the spelling or try a shorter search.</p>
            <Button variant="outline" className="mt-5" onClick={clearSearch}>
              Clear Search
            </Button>
          </div>
        )}

        {error && (
          <div className="mt-4">
            <FormAlert message={error} />
          </div>
        )}

        <DialogFooter className="mt-5">
          <DialogClose asChild>
            <Button variant="outline" disabled={saving}>
              Cancel
            </Button>
          </DialogClose>
          <LoadingButton pending={saving} pendingLabel="Saving…" disabled={unchanged} onClick={handleSave}>
            Save Target Role
          </LoadingButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
