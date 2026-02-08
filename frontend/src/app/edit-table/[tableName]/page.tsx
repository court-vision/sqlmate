"use client";

import React, { useEffect, useState, useCallback } from "react";
import { Header } from "@/components/header";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowLeft, RefreshCw, CheckCircle, AlertCircle } from "lucide-react";
import { useRouter, useParams } from "next/navigation";
import { tableService, queryService } from "@/services/api";
import { QueryResultTable } from "@/components/queryResultTable";
import { TableUpdatePanel } from "@/components/tableUpdatePanel";
import { toast } from "@/components/ui/use-toast";
import type {
  Table,
  TableUpdateAttribute,
  TableUpdateConstraint,
} from "@/types/http";

export default function EditTablePage() {
  // Use the useParams hook to get the tableName parameter
  const params = useParams();
  const tableName = params?.tableName as string;

  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);
  const [tableData, setTableData] = useState<Table | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [updateResult, setUpdateResult] = useState<{
    success: boolean;
    message: string;
    rowsAffected?: number;
  } | null>(null);

  // Transform columns from tableData to the format expected by TableUpdatePanel
  const columns = tableData
    ? tableData.columns.map((col) => ({ name: col, type: "" }))
    : [];

  const fetchTableData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await tableService.getTableData(tableName);
      setTableData(data.table!!);
    } catch (err: any) {
      setError(err.message || "Failed to fetch table data");

      // Handle unauthorized errors
      if (err.message.includes("UNAUTHORIZED")) {
        router.push("/sign-in");
        return;
      }
    } finally {
      setIsLoading(false);
    }
  }, [tableName, router]);

  const handleUpdateSubmit = async (
    updates: TableUpdateAttribute[],
    constraints: TableUpdateConstraint[]
  ) => {
    setIsSubmitting(true);
    setUpdateResult(null);
    setError(null);

    try {
      // Create the update request payload
      const updateData = {
        table: tableName,
        updates,
        constraints,
      };

      // Send the update request to the backend
      const result = await queryService.updateTable({
        query_params: updateData,
      });

      setUpdateResult({
        success: result.status.status === "success",
        message: result.status.message || "Table updated successfully",
        rowsAffected: result.rows_affected,
      });

      // Show success toast
      toast({
        title: "Update successful",
        description: `${result.rows_affected || 0} row(s) affected`,
        variant: "default",
      });

      // Refresh the table data to show the updated data
      fetchTableData();
    } catch (err: unknown) {
      const errorMessage =
        typeof err === "object" && err !== null && "error_msg" in err
          ? (err.error_msg as string)
          : err instanceof Error
          ? err.message
          : String(err);

      toast({
        title: "Update failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  useEffect(() => {
    fetchTableData();
  }, [fetchTableData]);

  return (
    <div className="flex flex-col h-screen">
      <Header />
      <div className="container mx-auto py-8 max-w-4xl flex-1">
        <div className="flex items-center mb-6">
          <Button
            variant="ghost"
            className="mr-4 glass hover:bg-white/10 transition-all-smooth"
            onClick={() => router.back()}
          >
            <ArrowLeft size={16} className="mr-2" />
            Back
          </Button>
          <h1 className="text-2xl font-bold gradient-text">
            Edit Table: {tableName}
          </h1>

          <Button
            variant="outline"
            className="ml-auto glass hover:bg-white/10 hover-glow transition-all-smooth"
            onClick={fetchTableData}
            disabled={isLoading}
          >
            <RefreshCw
              size={16}
              className={`mr-2 ${isLoading ? "animate-spin" : ""}`}
            />
            Refresh
          </Button>
        </div>

        {error && (
          <Card className="p-4 mb-6 glass border border-red-400/50 text-red-400 animate-slide-up">
            <div className="flex items-center">
              <AlertCircle size={16} className="mr-2" />
              <p>{error}</p>
            </div>
          </Card>
        )}

        {updateResult && updateResult.success && (
          <Card className="p-4 mb-6 glass border border-green-400/50 text-green-400 animate-slide-up">
            <div className="flex items-center">
              <CheckCircle size={16} className="mr-2" />
              <p>
                {updateResult.message}
                {updateResult.rowsAffected !== undefined &&
                  ` (${updateResult.rowsAffected} row${
                    updateResult.rowsAffected !== 1 ? "s" : ""
                  } affected)`}
              </p>
            </div>
          </Card>
        )}

        {/* Table Update Panel */}
        {!isLoading && tableData && (
          <TableUpdatePanel
            columns={columns}
            onSubmit={handleUpdateSubmit}
            isSubmitting={isSubmitting}
          />
        )}

        {isLoading ? (
          <div className="flex justify-center items-center p-12">
            <div className="spinner-gradient h-12 w-12"></div>
          </div>
        ) : (
          <div className="space-y-6">
            <Card className="p-6 glass hover-lift transition-all-smooth animate-slide-up">
              {tableData ? (
                <QueryResultTable data={tableData} />
              ) : (
                <p className="text-center text-muted-foreground">
                  No table data available
                </p>
              )}
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
