import { useEffect } from "react";

// Sets the browser tab title for the current page, such as "Create Account | KerjaReady"
export function usePageTitle(title: string) {
  useEffect(() => {
    document.title = title;
  }, [title]);
}
