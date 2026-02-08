"use client";

import { useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { BaseApiClient } from "@/services/api/baseClient";
import { setApiClientTokenGetter } from "@/lib/apiClient";

export function AuthInit() {
  const { getToken } = useAuth();

  useEffect(() => {
    const tokenGetter = () => getToken();
    BaseApiClient.setTokenGetter(tokenGetter);
    setApiClientTokenGetter(tokenGetter);
  }, [getToken]);

  return null;
}
