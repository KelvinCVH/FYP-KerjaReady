import { Amplify } from "aws-amplify";

// Connects Amplify Auth to the KerjaReady Cognito user pool. Call once before rendering.
export function configureAmplify() {
  const userPoolId = import.meta.env.VITE_USER_POOL_ID;
  const userPoolClientId = import.meta.env.VITE_USER_POOL_CLIENT_ID;

  if (!userPoolId || !userPoolClientId) {
    throw new Error(
      "Missing Cognito config: set VITE_USER_POOL_ID and VITE_USER_POOL_CLIENT_ID in frontend/.env.local (see .env.example).",
    );
  }

  Amplify.configure({
    Auth: {
      Cognito: {
        userPoolId,
        userPoolClientId,
        loginWith: { email: true },
        signUpVerificationMethod: "code",
      },
    },
  });
}
