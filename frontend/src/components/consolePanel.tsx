import { useState } from "react";
import { Button } from "@/components/ui/button";
import { QueryResultTable } from "@/components/queryResultTable";
import type { Table, SaveTableRequest } from "@/types/http";
import { useRouter } from "next/navigation";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { AlertCircle, SaveIcon } from "lucide-react";
import { postUserTable } from "@/lib/apiClient";
import { toast } from "./ui/use-toast";
import { useAuth } from "@clerk/nextjs";

export function ConsolePanel({
  consoleOutput,
  queryOutput,
}: {
  consoleOutput: Table | null;
  queryOutput: string | null;
}) {
  const [activeTab, setActiveTab] = useState<"results" | "query">("results");
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [tableName, setTableName] = useState("");
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveSuccess, setSaveSuccess] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const router = useRouter();
  const { isSignedIn } = useAuth();

  const handleSaveTable = async () => {
    // Check authentication first
    if (!isSignedIn) {
      toast({
        title: "Authentication Required",
        description: "Please sign in to save tables",
        variant: "destructive",
      });
      router.push("/sign-in");
      return;
    }

    if (!queryOutput) {
      setSaveError("No query results to save");
      return;
    }

    // Validate tablename
    if (!tableName.trim()) {
      setSaveError("Please enter a valid table name");
      return;
    }

    // Reset states
    setSaveError(null);
    setSaveSuccess(null);
    setIsSaving(true);

    try {
      // Create the request data
      const saveTableData: SaveTableRequest = {
        table_name: tableName.trim(),
        query: queryOutput,
      };

      // Send the request to save the table (no need to get the response here)
      await postUserTable(saveTableData);

      // Success
      setSaveSuccess(`Table "${tableName}" saved successfully!`);
      setTableName("");

      // Close dialog after a delay
      setTimeout(() => {
        setShowSaveDialog(false);
        setSaveSuccess(null);
      }, 800);
    } catch (error: any) {
      toast({
        title: "Save Failed",
        description: error.message || "Failed to save table",
        variant: "destructive",
      });
      console.error("Error saving table:", error);

      // Set error message for other errors
      setSaveError(error.message || "Failed to save table");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="h-full flex flex-col glass border-t border-border">
      <div className="flex items-center justify-between px-4 h-10 flex-shrink-0">
        <div className="flex items-center space-x-4">
          <Button
            variant="secondary"
            size="sm"
            className={`text-sm px-3 py-1 h-auto transition-all-smooth ${
              activeTab === "results"
                ? "bg-primary text-primary-foreground"
                : "glass hover:bg-accent"
            }`}
            onClick={() => setActiveTab("results")}
          >
            Results
          </Button>
          <Button
            variant="secondary"
            size="sm"
            className={`text-sm px-3 py-1 h-auto transition-all-smooth ${
              activeTab === "query"
                ? "bg-primary text-primary-foreground"
                : "glass hover:bg-accent"
            }`}
            onClick={() => setActiveTab("query")}
          >
            Query
          </Button>
        </div>

        {/* Save Table Button */}
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="outline"
                size="sm"
                className="text-sm px-3 py-1 h-auto flex items-center gap-1 glass hover:bg-primary/20 hover-glow transition-all-smooth"
                onClick={() => setShowSaveDialog(true)}
                disabled={!consoleOutput || !queryOutput || !isSignedIn}
              >
                <SaveIcon size={14} /> Save Table
              </Button>
            </TooltipTrigger>
            {!isSignedIn && (
              <TooltipContent>
                <p>Please sign in to save tables</p>
              </TooltipContent>
            )}
          </Tooltip>
        </TooltipProvider>
      </div>
      <div className="flex-1 min-h-0 p-4 overflow-auto">
        {activeTab === "results" ? (
          <div className="font-mono text-sm p-3 glass rounded animate-slide-up min-h-full">
            {consoleOutput?.error ? (
              <div className="p-4 rounded-md glass border border-red-400/50 text-red-400">
                <div className="flex items-center">
                  <AlertCircle className="h-5 w-5 mr-2" />
                  <span className="font-medium">Query Error: </span>
                  <span className="ml-1">{consoleOutput.error}</span>
                </div>
              </div>
            ) : consoleOutput ? (
              <QueryResultTable data={consoleOutput} itemsPerPage={10} />
            ) : (
              <p className="text-muted-foreground">No results to display</p>
            )}
          </div>
        ) : (
          <div className="font-mono text-sm p-3 glass rounded h-full animate-slide-up">
            {queryOutput ? (
              <pre className="whitespace-pre-wrap break-words">
                {queryOutput}
              </pre>
            ) : (
              <p className="text-muted-foreground">No query to display</p>
            )}
          </div>
        )}
      </div>

      {/* Save Table Dialog */}
      <Dialog open={showSaveDialog} onOpenChange={setShowSaveDialog}>
        <DialogContent className="sm:max-w-[425px] glass-panel">
          <DialogHeader>
            <DialogTitle className="gradient-text">Save Table</DialogTitle>
            <DialogDescription>
              Enter a name for your table. This table will be saved to your
              account and can be accessed later.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label htmlFor="tableName" className="text-sm font-medium">
                Table Name
              </label>
              <Input
                id="tableName"
                placeholder="my_custom_table"
                value={tableName}
                onChange={(e) => {
                  setTableName(e.target.value);
                  setSaveError(null);
                }}
                className={`glass-input transition-all-smooth ${
                  saveError
                    ? "border-red-500 focus:ring-red-500"
                    : "focus:ring-primary"
                }`}
              />
              {saveError && <p className="text-sm text-red-400">{saveError}</p>}
              {saveSuccess && (
                <p className="text-sm text-green-400">{saveSuccess}</p>
              )}
            </div>
          </div>

          <DialogFooter>
            <DialogClose asChild>
              <Button
                variant="outline"
                disabled={isSaving}
                className="glass hover:bg-accent transition-all-smooth"
              >
                Cancel
              </Button>
            </DialogClose>
            <Button
              onClick={handleSaveTable}
              disabled={isSaving || !tableName.trim()}
              className="gradient-primary hover:shadow-lg hover:scale-105 transition-all-smooth"
            >
              {isSaving ? "Saving..." : "Save"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
