import { Amplify } from "aws-amplify";

// Connects Amplify Auth to the KerjaReady Cognito user pool. Call once before rendering.
export function configureAmplify() {
  const userPoolId = import.meta.env.VITE_USER_POOL_ID;
  const userPoolClientId = import.meta.env.VITE_USER_POOL_CLIENT_ID;
  const cognitoDomain = import.meta.env.VITE_COGNITO_DOMAIN;

  if (!userPoolId || !userPoolClientId || !cognitoDomain) {
    throw new Error(
      "Missing Cognito config: set VITE_USER_POOL_ID, VITE_USER_POOL_CLIENT_ID and VITE_COGNITO_DOMAIN in frontend/.env.local (see .env.example).",
    );
  }

  const origin = window.location.origin;

  Amplify.configure({
    Auth: {
      Cognito: {
        userPoolId,
        userPoolClientId,
        loginWith: {
          email: true,
          // Google sign-in through the Cognito domain (OAuth code flow)
          oauth: {
            domain: cognitoDomain,
            scopes: ["openid", "email", "profile"],
            redirectSignIn: [`${origin}/auth/callback`],
            redirectSignOut: [`${origin}/sign-in`],
            responseType: "code",
            providers: ["Google"],
          },
        },
        signUpVerificationMethod: "code",
      },
    },
  });
}
