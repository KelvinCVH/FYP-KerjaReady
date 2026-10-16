import { createBrowserRouter, Navigate } from "react-router";
import RequireRole from "./components/auth/RequireRole";
import SidebarLayout from "./layouts/SidebarLayout";
import type { NavItem } from "./layouts/SidebarLayout";

import LandingPage from "./pages/public/LandingPage";
import SignInPage from "./pages/public/SignInPage";
import AuthCallbackPage from "./pages/public/AuthCallbackPage";
import ForgotPasswordPage from "./pages/public/ForgotPasswordPage";
import ResetPasswordPage from "./pages/public/ResetPasswordPage";
import RegisterPage from "./pages/public/RegisterPage";
import AccountDetailsPage from "./pages/public/AccountDetailsPage";
import VerifyEmailPage from "./pages/public/VerifyEmailPage";
import NotFoundPage from "./pages/public/NotFoundPage";
import PrivacyNoticePage from "./pages/public/PrivacyNoticePage";

import CandidateDashboardPage from "./pages/candidate/CandidateDashboardPage";
import ResumePage from "./pages/candidate/ResumePage";
import SelectTargetRolePage from "./pages/candidate/SelectTargetRolePage";
import ResumeResultPage from "./pages/candidate/ResumeResultPage";
import SkillGapPage from "./pages/candidate/SkillGapPage";
import RoadmapPage from "./pages/candidate/RoadmapPage";
import JobsPage from "./pages/candidate/JobsPage";
import CandidateApplicationsPage from "./pages/candidate/CandidateApplicationsPage";
import CandidateProfilePage from "./pages/candidate/CandidateProfilePage";

import RecruiterDashboardPage from "./pages/recruiter/RecruiterDashboardPage";
import ListingsPage from "./pages/recruiter/ListingsPage";
import CreateListingPage from "./pages/recruiter/CreateListingPage";
import ListingApplicantsPage from "./pages/recruiter/ListingApplicantsPage";
import EditListingPage from "./pages/recruiter/EditListingPage";

const candidateNavItems: NavItem[] = [
  { label: "Dashboard", to: "/candidate/dashboard" },
  { label: "Resume", to: "/candidate/resume" },
  { label: "Skill Gap", to: "/candidate/skill-gap" },
  { label: "Roadmap", to: "/candidate/roadmap" },
  { label: "Jobs", to: "/candidate/jobs" },
  { label: "Applications", to: "/candidate/applications" },
  { label: "Profile", to: "/candidate/profile" },
];

const recruiterNavItems: NavItem[] = [
  { label: "Dashboard", to: "/recruiter/dashboard" },
  { label: "Listings", to: "/recruiter/listings" },
];

export const router = createBrowserRouter([
  { path: "/", element: <LandingPage /> },
  { path: "/sign-in", element: <SignInPage /> },
  { path: "/auth/callback", element: <AuthCallbackPage /> },
  { path: "/forgot-password", element: <ForgotPasswordPage /> },
  { path: "/reset-password", element: <ResetPasswordPage /> },
  { path: "/register", element: <RegisterPage /> },
  {
    path: "/register/candidate",
    element: <AccountDetailsPage key="candidate" accountType="candidate" />,
  },
  {
    path: "/register/recruiter",
    element: <AccountDetailsPage key="recruiter" accountType="recruiter" />,
  },
  { path: "/register/verify", element: <VerifyEmailPage /> },
  { path: "/privacy", element: <PrivacyNoticePage /> },
  {
    path: "/candidate",
    element: (
      <RequireRole key="candidate" role="candidate">
        <SidebarLayout navItems={candidateNavItems} />
      </RequireRole>
    ),
    children: [
      { index: true, element: <Navigate to="dashboard" replace /> },
      { path: "dashboard", element: <CandidateDashboardPage /> },
      { path: "resume", element: <ResumePage /> },
      { path: "resume/target-role", element: <SelectTargetRolePage /> },
      { path: "resume/result", element: <ResumeResultPage /> },
      { path: "skill-gap", element: <SkillGapPage /> },
      { path: "roadmap", element: <RoadmapPage /> },
      { path: "jobs", element: <JobsPage /> },
      { path: "jobs/:listingId", element: <JobsPage /> },
      { path: "applications", element: <CandidateApplicationsPage /> },
      { path: "profile", element: <CandidateProfilePage /> },
    ],
  },
  {
    path: "/recruiter",
    element: (
      <RequireRole key="recruiter" role="recruiter">
        <SidebarLayout navItems={recruiterNavItems} />
      </RequireRole>
    ),
    children: [
      { index: true, element: <Navigate to="dashboard" replace /> },
      { path: "dashboard", element: <RecruiterDashboardPage /> },
      { path: "listings", element: <ListingsPage /> },
      { path: "listings/new", element: <CreateListingPage /> },
      { path: "listings/:listingId", element: <ListingApplicantsPage /> },
      { path: "listings/:listingId/edit", element: <EditListingPage /> },
    ],
  },
  { path: "*", element: <NotFoundPage /> },
]);