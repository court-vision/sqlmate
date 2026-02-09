"use client";

import { useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { BaseApiClient } from "@/services/api/baseClient";
import { setApiClientTokenGetter } from "@/lib/apiClient";
import { useEmbeddedAuth } from "@/hooks/useEmbeddedAuth";

export function AuthInit() {
  const { getToken } = useAuth();

  // Activate embedded mode listener (postMessage for auth tokens + theme sync)
  useEmbeddedAuth();

  useEffect(() => {
    const tokenGetter = () => getToken();
    BaseApiClient.setTokenGetter(tokenGetter);
    setApiClientTokenGetter(tokenGetter);
  }, [getToken]);

  return null;
}
