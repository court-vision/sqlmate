"use client";

import { useEffect, useState } from "react";
// import {
//   getTables,
//   deleteUserTables,
//   getTableDataForExport,
// } from "@/lib/apiClient";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { TrashIcon, RefreshCw, PencilIcon, Download } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { Header } from "@/components/header";
import { Checkbox } from "@/components/ui/checkbox";
import { toast } from "@/components/ui/use-toast";
import { useRouter } from "next/navigation";
import { downloadTableAsCSV } from "@/utils/csv";
import { tableService } from "@/services/api";

interface UserTable {
  table_name: string;
  created_at: string;
}

export default function MyTablesPage() {
  const router = useRouter();
  const [tables, setTables] = useState<UserTable[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTables, setSelectedTables] = useState<string[]>([]);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [downloadLoading, setDownloadLoading] = useState<string | null>(null);

  const fetchTables = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await tableService.getTables();
      setTables(data.tables || []);
      // Clear selections when refreshing
      setSelectedTables([]);
    } catch (err: any) {
      console.log(err);

      toast({
        title: "Error fetching tables",
        description: err.message || "Failed to load tables",
        variant: "destructive",
      });

      setError(err.message || "Failed to load tables");
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggleSelection = (tableName: string) => {
    setSelectedTables((prev) =>
      prev.includes(tableName)
        ? prev.filter((name) => name !== tableName)
        : [...prev, tableName]
    );
  };

  const handleSelectAll = () => {
    if (selectedTables.length === tables.length) {
      setSelectedTables([]);
    } else {
      setSelectedTables(tables.map((table) => table.table_name));
    }
  };

  const handleDeleteTable = async (tableName: string) => {
    setDeleteLoading(true);
    try {
      const response = await tableService.deleteTables({
        table_names: [tableName],
      });

      // Remove deleted table from the list
      setTables((prev) =>
        prev.filter((table) => table.table_name !== tableName)
      );
      // Remove from selected tables if it was selected
      setSelectedTables((prev) => prev.filter((name) => name !== tableName));
      toast({
        title: "Table deleted",
        description: `Successfully deleted table: ${tableName}`,
      });
    } catch (err: any) {
      setError(err.message || "Failed to delete table");
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleBulkDelete = async () => {
    if (selectedTables.length === 0) return;

    setDeleteLoading(true);
    try {
      const response = await tableService.deleteTables({
        table_names: selectedTables,
      });

      setTables((prev) =>
        prev.filter((table) => !selectedTables.includes(table.table_name))
      );
      // Clear selections
      setSelectedTables([]);
      toast({
        title: "Tables deleted",
        description: `Successfully deleted ${
          response.deleted_tables!!.length
        } tables`,
      });
    } catch (err: any) {
      setError(err.message || "Failed to delete table");
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleEditTable = (tableName: string) => {
    // For now, we'll just navigate to a placeholder route
    router.push(`/edit-table/${tableName}`);
  };

  const handleDownloadCSV = async (tableName: string) => {
    setDownloadLoading(tableName);
    try {
      const tableData = await tableService.getTableDataForExport(tableName);

      // Create a new table with the same structure but convert rows from arrays to objects
      if (tableData.table) {
        const originalTable = tableData.table;

        // Create a modified table with rows as objects instead of arrays
        const modifiedTable = {
          ...originalTable,
          rows: originalTable.rows.map((row) => {
            // Convert each row from array to object using column names as keys
            const rowObject: Record<string, any> = {};
            originalTable.columns.forEach((column, index) => {
              rowObject[column] = row[index];
            });
            return rowObject;
          }),
        };

        downloadTableAsCSV(modifiedTable, tableName);
        toast({
          title: "Download successful",
          description: `${tableName}.csv has been downloaded`,
        });
      } else {
        throw new Error("No table data received");
      }
    } catch (err: any) {
      setError(err.message || "Failed to download table");
      toast({
        title: "Download failed",
        description: err.message || "Failed to download table",
        variant: "destructive",
      });
    } finally {
      setDownloadLoading(null);
    }
  };

  useEffect(() => {
    fetchTables();
  }, []);

  return (
    <div className="flex flex-col h-screen">
      <Header />
      <div className="container mx-auto py-8 max-w-4xl flex-1">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold gradient-text">My Saved Tables</h1>
          <div className="flex gap-2">
            {selectedTables.length > 0 && (
              <Button
                variant="destructive"
                onClick={handleBulkDelete}
                disabled={deleteLoading}
                className="flex items-center gap-2 glass hover:bg-red-500/20 hover-glow transition-all-smooth"
              >
                <TrashIcon size={16} />
                Delete Selected ({selectedTables.length})
              </Button>
            )}
            <Button
              variant="outline"
              onClick={fetchTables}
              disabled={isLoading}
              className="flex items-center gap-2 glass hover:bg-white/10 hover-glow transition-all-smooth"
            >
              <RefreshCw
                size={16}
                className={isLoading ? "animate-spin" : ""}
              />
              Refresh
            </Button>
          </div>
        </div>

        {error && (
          <Card className="p-4 mb-6 glass border border-red-400/50 text-red-400 animate-slide-up">
            <p>{error}</p>
          </Card>
        )}

        {isLoading ? (
          <div className="flex justify-center items-center p-12">
            <div className="spinner-gradient h-12 w-12"></div>
          </div>
        ) : tables.length === 0 ? (
          <Card className="p-6 text-center glass hover-lift transition-all-smooth animate-slide-up">
            <p className="text-muted-foreground mb-4">
              You don&apos;t have any saved tables yet.
            </p>
            <p className="text-sm">
              Run a query and click the &quot;Save Table&quot; button to save
              your results.
            </p>
          </Card>
        ) : (
          <div className="overflow-hidden rounded-md glass animate-slide-up">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-white/5 border-b border-white/10">
                  <th className="py-3 px-4 text-left font-medium w-10">
                    <Checkbox
                      checked={
                        selectedTables.length === tables.length &&
                        tables.length > 0
                      }
                      onCheckedChange={handleSelectAll}
                      aria-label="Select all tables"
                    />
                  </th>
                  <th className="py-3 px-4 text-left font-medium gradient-text">
                    Table Name
                  </th>
                  <th className="py-3 px-4 text-left font-medium gradient-text">
                    Created
                  </th>
                  <th className="py-3 px-4 text-right font-medium gradient-text">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {tables.map((table, index) => (
                  <tr
                    key={table.table_name}
                    className={`${
                      index % 2 === 0 ? "bg-white/5" : "bg-white/10"
                    } hover:bg-white/15 transition-all-smooth`}
                  >
                    <td className="py-3 px-4">
                      <Checkbox
                        checked={selectedTables.includes(table.table_name)}
                        onCheckedChange={() =>
                          handleToggleSelection(table.table_name)
                        }
                        aria-label={`Select ${table.table_name}`}
                      />
                    </td>
                    <td className="py-3 px-4 font-medium">
                      {table.table_name}
                    </td>
                    <td className="py-3 px-4 text-muted-foreground">
                      {formatDistanceToNow(new Date(table.created_at + "Z"), {
                        addSuffix: true,
                      })}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex justify-end space-x-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 w-8 p-0 hover:bg-blue-500/20 hover-glow transition-all-smooth"
                          onClick={() => handleEditTable(table.table_name)}
                        >
                          <PencilIcon size={16} className="text-blue-400" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 w-8 p-0 hover:bg-red-500/20 hover-glow transition-all-smooth"
                          onClick={() => handleDeleteTable(table.table_name)}
                          disabled={deleteLoading}
                        >
                          <TrashIcon size={16} className="text-red-400" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 w-8 p-0 hover:bg-green-500/20 hover-glow transition-all-smooth"
                          onClick={() => handleDownloadCSV(table.table_name)}
                          disabled={downloadLoading === table.table_name}
                        >
                          <Download size={16} className="text-green-400" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
