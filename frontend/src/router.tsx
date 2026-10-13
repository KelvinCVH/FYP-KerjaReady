import { createBrowserRouter, Navigate } from "react-router";
import SidebarLayout from "./layouts/SidebarLayout";
import type { NavItem } from "./layouts/SidebarLayout";

import SignInPage from "./pages/public/SignInPage";
import SignUpPage from "./pages/public/SignUpPage";
import NotFoundPage from "./pages/public/NotFoundPage";

import CandidateDashboardPage from "./pages/candidate/CandidateDashboardPage";
import ResumePage from "./pages/candidate/ResumePage";
import SelectTargetRolePage from "./pages/candidate/SelectTargetRolePage";
import ResumeResultPage from "./pages/candidate/ResumeResultPage";
import SkillGapPage from "./pages/candidate/SkillGapPage";
import RoadmapPage from "./pages/candidate/RoadmapPage";
import JobsPage from "./pages/candidate/JobsPage";
import CandidateApplicationsPage from "./pages/candidate/CandidateApplicationsPage";

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
];

const recruiterNavItems: NavItem[] = [
  { label: "Dashboard", to: "/recruiter/dashboard" },
  { label: "Listings", to: "/recruiter/listings" },
];

export const router = createBrowserRouter([
  // Sends users to sign-in for now; the sign-in story will redirect signed-in users to their dashboard
  { path: "/", element: <Navigate to="/sign-in" replace /> },
  { path: "/sign-in", element: <SignInPage /> },
  { path: "/sign-up", element: <SignUpPage /> },
  {
    path: "/candidate",
    element: <SidebarLayout navItems={candidateNavItems} />,
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
    ],
  },
  {
    path: "/recruiter",
    element: <SidebarLayout navItems={recruiterNavItems} />,
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