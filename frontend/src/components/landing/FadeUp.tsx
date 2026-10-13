import type { ReactNode } from "react";
import { LazyMotion, domAnimation, useReducedMotion } from "motion/react";
import * as m from "motion/react-m";

type FadeUpProps = {
  children: ReactNode;
  className?: string;
};

// One-time entry animation for landing sections (DESIGN.md Section 12).
// LazyMotion with domAnimation keeps the bundle small; domAnimation includes whileInView.
export default function FadeUp({ children, className }: FadeUpProps) {
  const shouldReduceMotion = useReducedMotion();

  return (
    <LazyMotion features={domAnimation} strict>
      <m.div
        className={className}
        initial={shouldReduceMotion ? false : { opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, amount: 0.2 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
      >
        {children}
      </m.div>
    </LazyMotion>
  );
}
