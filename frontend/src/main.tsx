import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router/dom";
import "@fontsource-variable/geist";
import "@fontsource-variable/geist-mono";
// Completes Google sign-in when Cognito redirects back to /auth/callback
import "aws-amplify/auth/enable-oauth-listener";
import { configureAmplify } from "./lib/amplify";
import { router } from "./router";
import "./index.css";

configureAmplify();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
);