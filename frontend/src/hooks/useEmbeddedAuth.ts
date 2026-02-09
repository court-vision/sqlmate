"use client";

import { useState, useEffect } from "react";

const ALLOWED_ORIGINS = [
  "https://courtvision.dev",
  "https://www.courtvision.dev",
  "http://localhost:3001",
  "http://localhost:3000",
];

interface ThemeSyncPayload {
  mode: "light" | "dark";
  provider: "espn" | "yahoo";
  variables: Record<string, string>;
}

function applyTheme(payload: ThemeSyncPayload) {
  const root = document.documentElement;

  // Apply light/dark mode class
  root.classList.toggle("dark", payload.mode === "dark");

  // Court Vision sends HSL triplets (e.g. "20 20% 4%"), wrap in hsl()
  for (const [key, value] of Object.entries(payload.variables)) {
    root.style.setProperty(key, `hsl(${value})`);
  }

  // Override the fixed gradient background with the themed color
  document.body.style.background = `hsl(${payload.variables["--background"]})`;
}

export function useEmbeddedAuth() {
  const [isEmbedded, setIsEmbedded] = useState(false);

  useEffect(() => {
    const embedded =
      new URLSearchParams(window.location.search).get("embedded") === "true";
    setIsEmbedded(embedded);

    if (!embedded) return;

    function handleMessage(event: MessageEvent) {
      if (!ALLOWED_ORIGINS.includes(event.origin)) return;

      if (event.data?.type === "clerk-token" && event.data?.token) {
        sessionStorage.setItem("clerk-token", event.data.token);
      }

      if (event.data?.type === "theme-sync" && event.data?.payload) {
        applyTheme(event.data.payload as ThemeSyncPayload);
      }
    }

    window.addEventListener("message", handleMessage);

    // Notify parent that we're ready to receive messages
    window.parent.postMessage({ type: "sqlmate-ready" }, "*");

    return () => window.removeEventListener("message", handleMessage);
  }, []);

  return { isEmbedded };
}
