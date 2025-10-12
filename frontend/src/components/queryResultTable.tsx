import React from "react";
import type { Table } from "@/types/http";
import { AlertCircle } from "lucide-react";

type Props = {
  data: Table;
};

export const QueryResultTable: React.FC<Props> = ({ data }) => {
  const { columns, rows, error } = data;

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

  return (
    <div className="overflow-x-auto rounded-xl glass border border-white/10 shadow-lg">
      <table className="min-w-full text-sm text-left">
        <thead className="bg-white/5 border-b border-white/10">
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
          {rows.map((row, i) => (
            <tr
              key={i}
              className={`hover:bg-white/10 transition-all-smooth ${
                i % 2 === 0 ? "bg-white/5" : "bg-white/10"
              }`}
            >
              {row.map((value: any, j: number) => (
                <td
                  key={`${i}-${j}`}
                  className="px-4 py-2 border-b border-white/5 text-white"
                >
                  {String(value)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
