"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/authContext";
import { Header } from "@/components/header";
import { authService } from "@/services/api";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { toast } from "@/components/ui/use-toast";

export default function ProfilePage() {
  const { user, loading, logout, isAuthenticated } = useAuth();
  const router = useRouter();
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push("/login");
    }
  }, [loading, isAuthenticated, router]);

  if (loading) {
    return <p className="p-4 text-center">Loading profile…</p>;
  }

  if (!user) {
    return null; // This will redirect in the useEffect
  }

  const handleDeleteAccount = async () => {
    setIsDeleting(true);
    try {
      await authService.deleteUser();
      toast({
        title: "Account deleted",
        description: "Your account has been successfully deleted.",
      });
      logout(); // Log the user out after successful deletion
      router.push("/"); // Redirect to home page
    } catch (err: any) {
      toast({
        title: "Error",
        description: err.message || "Failed to delete account",
        variant: "destructive",
      });
      setIsDeleting(false); // Only reset if there was an error
    }
  };

  return (
    <div className="flex flex-col h-screen w-full">
      <Header />
      <div className="max-w-md mx-auto p-6 space-y-6 glass-card hover-lift transition-all-smooth mt-10 animate-slide-up">
        <h1 className="text-2xl font-semibold gradient-text">Profile</h1>
        <div className="space-y-4 p-4 glass rounded-lg">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 gradient-primary rounded-full flex items-center justify-center text-white font-bold text-lg">
              {user.username.charAt(0).toUpperCase()}
            </div>
            <div>
              <p className="font-medium">{user.username}</p>
              <p className="text-sm text-muted-foreground">{user.email}</p>
            </div>
          </div>
        </div>
        <div className="flex flex-col space-y-4 pt-4">
          <Button
            variant="destructive"
            onClick={logout}
            className="glass hover:bg-red-500/20 hover-glow transition-all-smooth"
          >
            Logout
          </Button>
          <Button
            variant="outline"
            className="glass border-red-400/50 text-red-400 hover:bg-red-500/20 hover:text-red-300 hover-glow transition-all-smooth"
            onClick={() => setShowDeleteConfirmation(true)}
            disabled={isDeleting}
          >
            {isDeleting ? (
              <div className="flex items-center gap-2">
                <div className="spinner-gradient w-4 h-4"></div>
                Deleting...
              </div>
            ) : (
              "Delete Account"
            )}
          </Button>
        </div>

        <AlertDialog
          open={showDeleteConfirmation}
          onOpenChange={setShowDeleteConfirmation}
        >
          <AlertDialogContent className="glass-panel">
            <AlertDialogHeader>
              <AlertDialogTitle className="gradient-text">
                Are you absolutely sure?
              </AlertDialogTitle>
              <AlertDialogDescription>
                This action cannot be undone. This will permanently delete your
                account and all data associated with it.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel className="glass hover:bg-white/10 transition-all-smooth">
                Cancel
              </AlertDialogCancel>
              <AlertDialogAction
                onClick={handleDeleteAccount}
                className="gradient-accent hover:shadow-lg hover:scale-105 transition-all-smooth"
              >
                Delete Account
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </div>
  );
}
