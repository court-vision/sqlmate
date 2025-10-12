"use client";

import Link from "next/link";
import { useAuth } from "@/contexts/authContext";
import { Avatar } from "./ui/avatar";
import { Button } from "./ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "./ui/dropdown-menu";
import { User, Table, LogOut } from "lucide-react";
import { useRouter } from "next/navigation";

export function Header() {
  const { user, isAuthenticated, logout } = useAuth();
  const router = useRouter();

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

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
          {isAuthenticated ? (
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">
                Welcome, {user?.username}!
              </span>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Avatar className="h-8 w-8 gradient-primary text-white cursor-pointer flex items-center justify-center hover-glow transition-all-smooth border-2 border-transparent hover:border-white/20">
                    {user?.username?.charAt(0).toUpperCase() || "U"}
                  </Avatar>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="glass-panel">
                  <DropdownMenuItem
                    onClick={() => router.push("/profile")}
                    className="hover:bg-white/10 transition-all-smooth"
                  >
                    <User className="mr-2 h-4 w-4" />
                    <span>Profile</span>
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => router.push("/my-tables")}
                    className="hover:bg-white/10 transition-all-smooth"
                  >
                    <Table className="mr-2 h-4 w-4" />
                    <span>My Tables</span>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator className="bg-white/10" />
                  <DropdownMenuItem
                    onClick={handleLogout}
                    className="hover:bg-red-500/20 text-red-400 transition-all-smooth"
                  >
                    <LogOut className="mr-2 h-4 w-4" />
                    <span>Logout</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Link href="/login">
                <Button
                  variant="outline"
                  className="glass-input hover-glow transition-all-smooth"
                >
                  Sign In
                </Button>
              </Link>
              <Link href="/register">
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
