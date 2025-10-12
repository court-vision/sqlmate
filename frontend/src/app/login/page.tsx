"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { Header } from "@/components/header";
import { authService } from "@/services/api";
import { toast } from "@/components/ui/use-toast";
import { useAuth } from "@/contexts/authContext";

export default function LoginPage() {
  const router = useRouter();
  const { setToken, setUser } = useAuth();
  const [form, setForm] = useState({ username: "", password: "" });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const onChange = (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm({ ...form, [e.target.name]: e.target.value });

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await authService.login(form.username, form.password);
      const token = response.token!!;

      localStorage.setItem("token", token);
      setToken(token);

      const userInfo = await authService.getCurrentUser();
      setUser({
        username: userInfo.username!!,
        email: userInfo.email!!,
      });

      toast({
        title: "Login successful!",
        description: "Welcome back! Redirecting to the home screen.",
        variant: "default",
      });

      router.push("/");
    } catch (err: any) {
      console.error("Login error:", err);

      // Show error toast
      toast({
        title: "Login failed",
        description: err.message || "Please check your credentials.",
        variant: "destructive",
      });

      setError(err.message || "Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col min-h-screen relative overflow-hidden">
      {/* Animated background particles */}
      <div className="absolute inset-0 opacity-20">
        <div className="absolute top-1/4 left-1/4 w-3 h-3 bg-blue-400 rounded-full animate-pulse-slow"></div>
        <div
          className="absolute top-3/4 right-1/4 w-2 h-2 bg-purple-400 rounded-full animate-pulse-slow"
          style={{ animationDelay: "1s" }}
        ></div>
        <div
          className="absolute top-1/2 left-3/4 w-2.5 h-2.5 bg-cyan-400 rounded-full animate-pulse-slow"
          style={{ animationDelay: "2s" }}
        ></div>
        <div
          className="absolute top-1/6 right-1/3 w-2 h-2 bg-pink-400 rounded-full animate-pulse-slow"
          style={{ animationDelay: "0.5s" }}
        ></div>
        <div
          className="absolute bottom-1/4 left-1/6 w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse-slow"
          style={{ animationDelay: "1.5s" }}
        ></div>
      </div>

      <Header />
      <div className="flex-1 flex items-center justify-center py-10 relative z-10">
        <form
          onSubmit={onSubmit}
          className="max-w-sm mx-auto p-8 space-y-6 glass-card hover-lift transition-all-smooth animate-slide-up"
        >
          <h2 className="text-2xl font-bold text-center gradient-text">
            Sign In
          </h2>
          {error && (
            <p className="text-sm text-red-400 bg-red-500/10 p-2 rounded border border-red-400/30">
              {error}
            </p>
          )}
          {["username", "password"].map((field) => (
            <div key={field}>
              <label className="block text-sm font-medium mb-2 capitalize">
                {field}
              </label>
              <input
                name={field}
                type={field === "password" ? "password" : "text"}
                value={field === "username" ? form.username : form.password}
                onChange={onChange}
                required
                className={cn(
                  "w-full p-3 glass-input rounded-lg transition-all-smooth",
                  "focus:outline-none focus:ring-2 focus:ring-primary focus:scale-105"
                )}
              />
            </div>
          ))}
          <Button
            type="submit"
            className="w-full gradient-primary hover:shadow-lg hover:scale-105 transition-all-smooth"
            disabled={loading}
          >
            {loading ? (
              <div className="flex items-center gap-2">
                <div className="spinner-gradient w-4 h-4"></div>
                Signing In…
              </div>
            ) : (
              "Sign In"
            )}
          </Button>
          <div className="text-center text-sm">
            Don&apos;t have an account?{" "}
            <Link
              href="/register"
              className="text-primary hover:text-primary/80 hover:underline transition-all-smooth"
            >
              Register
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}
