import AudiencePanels from "@/components/landing/AudiencePanels";
import FairAndPrivateSection from "@/components/landing/FairAndPrivateSection";
import HeroSection from "@/components/landing/HeroSection";
import HowItWorksSection from "@/components/landing/HowItWorksSection";
import LandingFooter from "@/components/landing/LandingFooter";
import LandingHeader from "@/components/landing/LandingHeader";
import { usePageTitle } from "@/hooks/usePageTitle";

export default function LandingPage() {
  usePageTitle("KerjaReady");

  return (
    <div className="min-h-[100dvh] bg-background text-foreground">
      <a
        href="#main"
        className="sr-only focus-visible:not-sr-only focus-visible:absolute focus-visible:left-4 focus-visible:top-4 focus-visible:z-10 focus-visible:rounded-lg focus-visible:border focus-visible:border-input focus-visible:bg-card focus-visible:px-3 focus-visible:py-2 focus-visible:text-sm"
      >
        Skip to Content
      </a>

      <LandingHeader />

      <main id="main">
        <HeroSection />
        <HowItWorksSection />
        <AudiencePanels />
        <FairAndPrivateSection />
      </main>

      <LandingFooter />
    </div>
  );
}
