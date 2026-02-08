"use client";

import Link from "next/link";
import { useAuth, useUser, UserButton } from "@clerk/nextjs";
import { Button } from "./ui/button";
import { Table } from "lucide-react";
import { useRouter } from "next/navigation";
import { useSearchParams } from "next/navigation";

export function Header() {
  const { isSignedIn } = useAuth();
  const { user } = useUser();
  const router = useRouter();
  const searchParams = useSearchParams();
  const isEmbedded = searchParams.get("embedded") === "true";

  // Hide header entirely in embedded mode
  if (isEmbedded) return null;

  return (
    <header className="sticky top-0 z-50 w-full glass border-b animate-fade-in">
      <div className="h-14 flex items-center justify-between px-4">
        <div className="flex items-center pl-4">
          <Link
            href="/"
            className="text-2xl font-extrabold gradient-title hover-glow transition-all-smooth"
          >
            SQLMate
          </Link>
        </div>

        <div className="flex-1" />

        <div className="flex items-center gap-4 pr-4">
          {isSignedIn ? (
            <div className="flex items-center gap-3">
              <span className="text-sm text-muted-foreground">
                Welcome, {user?.firstName || user?.username || "User"}!
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => router.push("/my-tables")}
                className="hover:bg-white/10 transition-all-smooth"
              >
                <Table className="mr-2 h-4 w-4" />
                My Tables
              </Button>
              <UserButton afterSignOutUrl="/" />
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Link href="/sign-in">
                <Button
                  variant="outline"
                  className="glass-input hover-glow transition-all-smooth"
                >
                  Sign In
                </Button>
              </Link>
              <Link href="/sign-up">
                <Button className="gradient-primary hover:shadow-lg hover:scale-105 transition-all-smooth">
                  Register
                </Button>
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
