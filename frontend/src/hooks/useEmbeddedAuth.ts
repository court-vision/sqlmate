"use client";

import { useState, useEffect } from "react";
import { useSearchParams } from "next/navigation";

const ALLOWED_ORIGINS = [
  "https://courtvision.dev",
  "https://www.courtvision.dev",
  "http://localhost:3001",
  "http://localhost:3000",
];

export function useEmbeddedAuth() {
  const searchParams = useSearchParams();
  const [isEmbedded, setIsEmbedded] = useState(false);

  useEffect(() => {
    const embedded = searchParams.get("embedded") === "true";
    setIsEmbedded(embedded);

    if (!embedded) return;

    function handleMessage(event: MessageEvent) {
      if (!ALLOWED_ORIGINS.includes(event.origin)) return;
      if (event.data?.type === "clerk-token" && event.data?.token) {
        sessionStorage.setItem("clerk-token", event.data.token);
      }
    }

    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, [searchParams]);

  return { isEmbedded };
}
