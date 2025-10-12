import React, { useState, useEffect, useMemo } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  PlusIcon,
  Trash2Icon,
  ChevronDownIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  MinusIcon,
} from "lucide-react";
import { dbTables } from "./tablePanel";

// Define types for column data
export interface Column {
  name: string;
  type: string;
  alias: string;
  constraint: {
    operator: string;
    value: string;
  };
  groupBy: boolean;
  aggregate: string;
  orderBy: "NONE" | "ASC" | "DESC"; // Add order by
  id: string; // Unique identifier for each column
}

interface TableCustomizationPanelProps {
  tableName: string;
  columns: Omit<
    Column,
    "constraint" | "groupBy" | "aggregate" | "id" | "alias" | "orderBy"
  >[];
  onClose: () => void;
  onGroupByChange: (hasGroupBy: boolean) => void;
  onColumnsChange: (columns: Column[]) => void; // Add callback for column changes
  initialCustomColumns?: Column[]; // Add prop for initial custom columns
  showAggregation?: boolean; // Always show the column (true/false)
  isAggregationEnabled?: boolean; // Whether the aggregation functionality is enabled
}

// Regex pattern for valid SQL identifiers: must start with letter or underscore, followed by letters, numbers, or underscores
const VALID_ALIAS_PATTERN = /^[a-zA-Z_][a-zA-Z0-9_]*$/;

export function TableCustomizationPanel({
  tableName,
  columns: initialColumns,
  onClose,
  onGroupByChange,
  onColumnsChange,
  initialCustomColumns,
  showAggregation = true, // Default to true to always show the column
  isAggregationEnabled = false, // Default to disabled if not provided
}: TableCustomizationPanelProps) {
  // Create ref to track initial render
  const isInitialRender = React.useRef(true);

  // Transform initial columns to add the required properties or use initial custom columns if provided
  const [columns, setColumns] = useState<Column[]>(() => {
    if (initialCustomColumns && initialCustomColumns.length > 0) {
      return initialCustomColumns;
    }

    return initialColumns.map((col) => ({
      ...col,
      alias: "",
      constraint: { operator: "", value: "" },
      groupBy: false,
      aggregate: "",
      orderBy: "NONE", // Initialize order by as NONE
      id: `${tableName}-${col.name}-${Math.random().toString(36).substr(2, 9)}`,
    }));
  });

  // State for showing the add attribute mode
  const [showAddMode, setShowAddMode] = useState(false);
  // State to track which attributes are selected for adding
  const [selectedAttributes, setSelectedAttributes] = useState<
    Record<string, boolean>
  >({});
  // State to track alias validation errors
  const [aliasErrors, setAliasErrors] = useState<Record<string, boolean>>({});

  // Get all available columns from the schema for this table
  const allTableColumns = useMemo(() => {
    // Find the table from the dynamically loaded dbTables
    const tableData = dbTables.find((table) => table.name === tableName);
    return tableData ? tableData.columns : [];
  }, [tableName]); // Remove dbTables from dependencies since it doesn't change

  // Calculate which columns are not yet included
  const availableColumns = useMemo(() => {
    const currentColumnNames = columns.map((col) => col.name);
    return allTableColumns.filter(
      (col) => !currentColumnNames.includes(col.name)
    );
  }, [allTableColumns, columns]);

  // Track if any column has groupBy enabled
  useEffect(() => {
    const hasGroupBy = columns.some((col) => col.groupBy);
    onGroupByChange(hasGroupBy);
  }, [columns, onGroupByChange]);

  // Update parent component with columns changes
  useEffect(() => {
    // Skip initial render to avoid circular updates
    if (isInitialRender.current) {
      isInitialRender.current = false;
      return;
    }

    // Add a check to prevent unnecessary updates
    onColumnsChange(columns);
  }, [columns, onColumnsChange]);

  // Handle alias change
  const handleAliASChange = (id: string, alias: string) => {
    // Check if the alias is valid or empty
    const isValid = alias === "" || VALID_ALIAS_PATTERN.test(alias);

    // Update the aliasErrors state
    setAliasErrors((prev) => ({
      ...prev,
      [id]: !isValid,
    }));

    // Only update the alias if it's valid or empty
    if (isValid) {
      setColumns((cols) =>
        cols.map((col) => (col.id === id ? { ...col, alias } : col))
      );
    }
  };

  // Handle constraint operator change
  const handleConstraintOperatorChange = (id: string, operator: string) => {
    setColumns((cols) =>
      cols.map((col) =>
        col.id === id
          ? { ...col, constraint: { ...col.constraint, operator } }
          : col
      )
    );
  };

  // Handle constraint value change
  const handleConstraintValueChange = (id: string, value: string) => {
    setColumns((cols) =>
      cols.map((col) =>
        col.id === id
          ? { ...col, constraint: { ...col.constraint, value } }
          : col
      )
    );
  };

  // Handle group by change
  const handleGroupByChange = (id: string, checked: boolean) => {
    setColumns((cols) =>
      cols.map((col) => (col.id === id ? { ...col, groupBy: checked } : col))
    );
  };

  // Handle aggregate change
  const handleAggregateChange = (id: string, aggregate: string) => {
    setColumns((cols) =>
      cols.map((col) => (col.id === id ? { ...col, aggregate } : col))
    );
  };

  // Handle order by change - cycle through NONE -> ASC -> DESC -> NONE
  const handleOrderByChange = (id: string) => {
    const nextState = (
      current: "NONE" | "ASC" | "DESC"
    ): "NONE" | "ASC" | "DESC" => {
      switch (current) {
        case "NONE":
          return "ASC";
        case "ASC":
          return "DESC";
        case "DESC":
          return "NONE";
      }
    };

    let updatedColumnsResult: Column[] | null = null; // Variable to hold the updated columns

    setColumns((prevColumns) => {
      const newColumns = prevColumns.map((col) => {
        if (col.id === id) {
          return {
            ...col,
            orderBy: nextState(col.orderBy),
          };
        }
        return col;
      });
      updatedColumnsResult = newColumns; // Store the result for the synchronous call below
      return newColumns; // Update internal state
    });

    // Call parent update synchronously AFTER internal state update is queued
    // Use the captured result to ensure we pass the correct state
    if (updatedColumnsResult) {
      onColumnsChange(updatedColumnsResult);
    }
  };

  // Toggle add mode
  const toggleAddMode = () => {
    setShowAddMode(!showAddMode);
    if (!showAddMode) {
      // Initialize selected attributes when entering add mode
      const initialSelection: Record<string, boolean> = {};
      availableColumns.forEach((col) => {
        initialSelection[col.name] = false;
      });
      setSelectedAttributes(initialSelection);
    } else {
      // Clear selections when exiting add mode
      setSelectedAttributes({});
    }
  };

  // Toggle attribute selection
  const toggleAttributeSelection = (columnName: string) => {
    setSelectedAttributes((prev) => ({
      ...prev,
      [columnName]: !prev[columnName],
    }));
  };

  // Add selected attributes
  const addSelectedAttributes = () => {
    const selectedColumns = availableColumns.filter(
      (col) => selectedAttributes[col.name]
    );

    setColumns((cols) => [
      ...cols,
      ...selectedColumns.map((col) => ({
        name: col.name,
        type: col.type,
        alias: "",
        constraint: { operator: "", value: "" },
        groupBy: false,
        aggregate: "",
        orderBy: "NONE" as const,
        id: `${tableName}-${col.name}-${Math.random()
          .toString(36)
          .substr(2, 9)}`,
      })),
    ]);

    setShowAddMode(false);
    setSelectedAttributes({});
  };

  // Cancel add mode
  const cancelAddMode = () => {
    setShowAddMode(false);
    setSelectedAttributes({});
  };

  // Remove a column row
  const removeColumn = (id: string) => {
    setColumns((cols) => cols.filter((col) => col.id !== id));
  };

  return (
    <Card className="mb-4 p-2 glass hover-lift transition-all-smooth animate-slide-up">
      <div className="flex justify-between items-center border-b border-white/10 pb-2 mb-2">
        <h3 className="text-sm font-medium gradient-text">{tableName}</h3>
        <Button
          variant="ghost"
          size="sm"
          onClick={onClose}
          className="h-6 w-6 p-0 hover:bg-red-500/20 text-red-400 hover:text-red-300 transition-all-smooth"
        >
          ×
        </Button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/10">
              <th className="text-left py-1 pr-4 text-muted-foreground">
                Attribute
              </th>
              <th className="text-left py-1 pr-4 text-muted-foreground">
                Type
              </th>
              <th
                className="text-left py-1 pr-4 text-muted-foreground"
                colSpan={2}
              >
                Constraint
              </th>
              <th className="text-left py-1 pr-4 text-muted-foreground">
                Group By
              </th>
              {showAggregation && (
                <th className="text-left py-1 pr-4 w-[160px] text-muted-foreground">
                  {" "}
                  {/* Do not change this */}
                  <div className="flex items-center">
                    <span>Aggregate</span>
                    {!isAggregationEnabled && (
                      <span className="text-xs text-muted-foreground ml-1 whitespace-nowrap">
                        (disabled)
                      </span>
                    )}
                  </div>
                </th>
              )}
              <th className="text-left py-1 pr-4 text-center text-muted-foreground">
                <span title="Order By">Order</span>
              </th>
              <th className="text-left py-1 pr-4 w-8"></th>
            </tr>
          </thead>
          <tbody>
            {/* Existing columns */}
            {columns.map((column) => (
              <tr
                key={column.id}
                className="border-b border-white/10 hover:bg-white/5 transition-all-smooth"
              >
                <td className="py-1 px-2 w-[140px]">
                  <div className="flex flex-col gap-1">
                    <span className="text-xs font-medium gradient-text">
                      {column.name}
                    </span>
                    <div className="flex flex-col">
                      <input
                        type="text"
                        value={column.alias}
                        onChange={(e) =>
                          handleAliASChange(column.id, e.target.value)
                        }
                        placeholder="AS..."
                        className={`glass-input px-1 py-0.5 text-xs w-full transition-all-smooth ${
                          aliasErrors[column.id]
                            ? "border-red-500 focus:ring-red-500"
                            : "focus:ring-primary"
                        }`}
                      />
                      {aliasErrors[column.id] && (
                        <span className="text-xs text-red-400 mt-0.5">
                          Invalid format
                        </span>
                      )}
                    </div>
                  </div>
                </td>
                <td className="py-1 px-2 w-[80px]">
                  <span className="text-xs text-muted-foreground">
                    {column.type}
                  </span>
                </td>
                <td className="py-1 px-2 w-[100px]">
                  <select
                    className="glass-input px-1 py-0.5 text-xs w-full transition-all-smooth focus:ring-primary"
                    value={column.constraint.operator}
                    onChange={(e) =>
                      handleConstraintOperatorChange(column.id, e.target.value)
                    }
                  >
                    <option value="">-</option>
                    <option value="=">=</option>
                    <option value="<">{"<"}</option>
                    <option value=">">{">"}</option>
                    <option value="<=">{"<="}</option>
                    <option value=">=">{">="}</option>
                    <option value="!=">{"!="}</option>
                    <option value="PREFIX">{"PREFIX"}</option>
                    <option value="SUFFIX">{"SUFFIX"}</option>
                    <option value="SUBSTRING">{"SUBSTRING"}</option>
                  </select>
                </td>
                <td className="py-1 px-2 w-[200px]">
                  <input
                    type="text"
                    className="glass-input px-1 py-0.5 text-xs w-full transition-all-smooth focus:ring-primary"
                    placeholder="Value"
                    value={column.constraint.value}
                    onChange={(e) =>
                      handleConstraintValueChange(column.id, e.target.value)
                    }
                    disabled={!column.constraint.operator}
                  />
                </td>
                <td className="py-1 px-2 w-[60px] text-center">
                  <input
                    type="checkbox"
                    className="form-checkbox h-3 w-3 accent-primary"
                    checked={column.groupBy}
                    onChange={(e) =>
                      handleGroupByChange(column.id, e.target.checked)
                    }
                  />
                </td>
                {showAggregation && (
                  <td className="py-1 px-2 w-[160px]">
                    <select
                      className="glass-input px-1 py-0.5 text-xs w-full transition-all-smooth focus:ring-primary"
                      value={column.aggregate}
                      onChange={(e) =>
                        handleAggregateChange(column.id, e.target.value)
                      }
                      disabled={!isAggregationEnabled}
                    >
                      <option value="">-</option>
                      <option value="sum">sum</option>
                      <option value="avg">avg</option>
                      <option value="min">min</option>
                      <option value="max">max</option>
                      <option value="count">count</option>
                    </select>
                  </td>
                )}
                <td className="py-1 pr-2 w-[60px] text-center">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleOrderByChange(column.id)}
                    title={
                      column.orderBy === "NONE"
                        ? "No ordering"
                        : column.orderBy === "ASC"
                        ? "Sort ASCending"
                        : "Sort DESCending"
                    }
                    className="h-6 w-6 p-0 hover:bg-primary/20 transition-all-smooth"
                  >
                    {column.orderBy === "NONE" && <MinusIcon size={14} />}
                    {column.orderBy === "ASC" && (
                      <ArrowUpIcon size={14} className="text-primary" />
                    )}
                    {column.orderBy === "DESC" && (
                      <ArrowDownIcon size={14} className="text-primary" />
                    )}
                  </Button>
                </td>
                <td className="py-1 px-2 w-[40px]">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeColumn(column.id)}
                    className="h-5 w-5 p-0 text-muted-foreground hover:text-red-400 hover:bg-red-500/20 transition-all-smooth"
                  >
                    <Trash2Icon size={12} />
                  </Button>
                </td>
              </tr>
            ))}

            {/* Available columns in add mode */}
            {showAddMode &&
              availableColumns.map((column) => (
                <tr
                  key={`add-${column.name}`}
                  className={`border-b border-white/10 hover:bg-white/5 transition-all-smooth cursor-pointer ${
                    selectedAttributes[column.name]
                      ? "bg-primary/10"
                      : "opacity-60"
                  }`}
                  onClick={() => toggleAttributeSelection(column.name)}
                >
                  <td className="py-1 px-2 w-[140px]">
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        className="form-checkbox h-3 w-3 accent-primary"
                        checked={selectedAttributes[column.name] || false}
                        onChange={() => toggleAttributeSelection(column.name)}
                        onClick={(e) => e.stopPropagation()}
                      />
                      <span className="text-xs font-medium text-muted-foreground">
                        {column.name}
                      </span>
                    </div>
                  </td>
                  <td className="py-1 px-2 w-[80px]">
                    <span className="text-xs text-muted-foreground">
                      {column.type}
                    </span>
                  </td>
                  <td className="py-1 px-2 w-[100px]">
                    <span className="text-xs text-muted-foreground opacity-50">
                      -
                    </span>
                  </td>
                  <td className="py-1 px-2 w-[200px]">
                    <span className="text-xs text-muted-foreground opacity-50">
                      -
                    </span>
                  </td>
                  <td className="py-1 px-2 w-[60px] text-center">
                    <span className="text-xs text-muted-foreground opacity-50">
                      -
                    </span>
                  </td>
                  {showAggregation && (
                    <td className="py-1 px-2 w-[160px]">
                      <span className="text-xs text-muted-foreground opacity-50">
                        -
                      </span>
                    </td>
                  )}
                  <td className="py-1 pr-2 w-[60px] text-center">
                    <span className="text-xs text-muted-foreground opacity-50">
                      -
                    </span>
                  </td>
                  <td className="py-1 px-2 w-[40px]">
                    <span className="text-xs text-muted-foreground opacity-50">
                      -
                    </span>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      <div className="mt-2 flex justify-end gap-2">
        {showAddMode ? (
          <>
            <Button
              variant="ghost"
              size="sm"
              onClick={cancelAddMode}
              className="text-xs flex items-center gap-1 h-6 glass hover:bg-red-500/20 hover:text-red-400 transition-all-smooth"
            >
              Cancel
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={addSelectedAttributes}
              disabled={!Object.values(selectedAttributes).some(Boolean)}
              className={`text-xs flex items-center gap-1 h-6 glass hover:bg-primary/20 hover-glow transition-all-smooth ${
                !Object.values(selectedAttributes).some(Boolean)
                  ? "opacity-50 cursor-not-allowed"
                  : ""
              }`}
            >
              <PlusIcon size={12} /> Add Selected
            </Button>
          </>
        ) : (
          <Button
            variant="ghost"
            size="sm"
            onClick={toggleAddMode}
            disabled={availableColumns.length === 0}
            className={`text-xs flex items-center gap-1 h-6 glass hover:bg-primary/20 hover-glow transition-all-smooth ${
              availableColumns.length === 0
                ? "opacity-50 cursor-not-allowed"
                : ""
            }`}
          >
            <PlusIcon size={12} /> Add attribute
          </Button>
        )}
      </div>
    </Card>
  );
}
