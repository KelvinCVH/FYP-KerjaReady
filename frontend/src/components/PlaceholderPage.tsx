import type { ReactNode } from "react";
import { usePageTitle } from "@/hooks/usePageTitle";

type PlaceholderPageProps = {
  title: string;
  description: string;
  children?: ReactNode;
};

export default function PlaceholderPage({ title, description, children }: PlaceholderPageProps) {
  usePageTitle(`${title} | KerjaReady`);

  return (
    <section>
      <h1 className="text-2xl font-semibold">{title}</h1>
      <p className="mt-2 text-muted-foreground">{description}</p>
      {children && <div className="mt-6 flex flex-wrap gap-3">{children}</div>}
    </section>
  );
}