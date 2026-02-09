import React, { useState, useMemo } from "react";
import type { Table } from "@/types/http";
import { AlertCircle, ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";

type Props = {
  data: Table;
  itemsPerPage?: number;
};

export const QueryResultTable: React.FC<Props> = ({
  data,
  itemsPerPage = 20,
}) => {
  const { columns, rows, error } = data;
  const [currentPage, setCurrentPage] = useState(1);

  // Calculate pagination
  const totalPages = Math.ceil((rows?.length || 0) / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentRows = useMemo(() => {
    return rows?.slice(startIndex, endIndex) || [];
  }, [rows, startIndex, endIndex]);

  // Reset to first page when data changes
  React.useEffect(() => {
    setCurrentPage(1);
  }, [data]);

  const goToPage = (page: number) => {
    setCurrentPage(Math.max(1, Math.min(page, totalPages)));
  };

  const goToPreviousPage = () => {
    setCurrentPage((prev) => Math.max(1, prev - 1));
  };

  const goToNextPage = () => {
    setCurrentPage((prev) => Math.min(totalPages, prev + 1));
  };

  // If there's an error, display it prominently
  if (error) {
    return (
      <div className="p-4 rounded-md glass border border-red-400/50 text-red-400">
        <div className="flex items-center">
          <AlertCircle className="h-5 w-5 mr-2" />
          <span className="font-medium">Query Error: </span>
          <span className="ml-1">{error}</span>
        </div>
      </div>
    );
  }

  if (!columns || !rows || !columns.length || !rows.length)
    return <p className="text-muted-foreground">No results found.</p>;

  // Generate page numbers for pagination
  const getPageNumbers = () => {
    const pages = [];
    const maxVisiblePages = 5;

    if (totalPages <= maxVisiblePages) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      const start = Math.max(1, currentPage - 2);
      const end = Math.min(totalPages, start + maxVisiblePages - 1);

      if (start > 1) {
        pages.push(1);
        if (start > 2) pages.push("...");
      }

      for (let i = start; i <= end; i++) {
        pages.push(i);
      }

      if (end < totalPages) {
        if (end < totalPages - 1) pages.push("...");
        pages.push(totalPages);
      }
    }

    return pages;
  };

  return (
    <div className="space-y-4">
      {/* Results info */}
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <div>
          Showing {startIndex + 1}-{Math.min(endIndex, rows.length)} of{" "}
          {rows.length} results
        </div>
        <div>
          Page {currentPage} of {totalPages}
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-xl glass shadow-lg">
        <table className="min-w-full text-sm text-left">
          <thead className="bg-muted border-b border-border">
            <tr>
              {columns.map((col, index) => (
                <th
                  key={`col-${index}`}
                  className="px-4 py-2 font-semibold gradient-text"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {currentRows.map((row, i) => (
              <tr
                key={startIndex + i}
                className={`hover:bg-primary/10 transition-all-smooth ${
                  i % 2 === 0 ? "" : "bg-muted"
                }`}
              >
                {row.map((value: any, j: number) => (
                  <td
                    key={`${startIndex + i}-${j}`}
                    className="px-4 py-2 border-b border-border text-foreground"
                  >
                    {String(value)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center space-x-2 pt-4 pb-2">
          <Button
            variant="outline"
            size="sm"
            onClick={goToPreviousPage}
            disabled={currentPage === 1}
            className="glass hover:bg-accent transition-all-smooth"
          >
            <ChevronLeft size={16} />
            Previous
          </Button>

          <div className="flex items-center space-x-1">
            {getPageNumbers().map((page, index) => (
              <React.Fragment key={index}>
                {page === "..." ? (
                  <span className="px-2 text-muted-foreground">...</span>
                ) : (
                  <Button
                    variant={currentPage === page ? "default" : "outline"}
                    size="sm"
                    onClick={() => goToPage(page as number)}
                    className={`transition-all-smooth ${
                      currentPage === page
                        ? "bg-primary text-primary-foreground"
                        : "glass hover:bg-accent"
                    }`}
                  >
                    {page}
                  </Button>
                )}
              </React.Fragment>
            ))}
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={goToNextPage}
            disabled={currentPage === totalPages}
            className="glass hover:bg-accent transition-all-smooth"
          >
            Next
            <ChevronRight size={16} />
          </Button>
        </div>
      )}
    </div>
  );
};
