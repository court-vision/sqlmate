import { useState, useCallback, useMemo, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { runVisualQuery } from "@/services/queryService";
import { Table } from "@/types/http";
import { useDroppable } from "@dnd-kit/core";
import { TableCustomizationPanel, Column } from "./tableCustomizationPanel";
import { TableItem } from "./tablePanel";
import { ArrowUpIcon, ArrowDownIcon } from "lucide-react";

// Interface for order by priority item
interface OrderByItem {
  id: string;
  tableId: string;
  tableName: string;
  columnName: string;
  direction: "ASC" | "DESC";
}

interface StudioCanvasProps {
  setConsoleOutput: (output: Table) => void;
  setQueryOutput: (output: string) => void;
  droppedTables: TableItem[];
  setDroppedTables: React.Dispatch<React.SetStateAction<TableItem[]>>;
}

export function StudioCanvas({
  setConsoleOutput,
  setQueryOutput,
  droppedTables,
  setDroppedTables,
}: StudioCanvasProps) {
  const [anyTableHasGroupBy, setAnyTableHasGroupBy] = useState(false);
  // Removing unused state variable
  const [_, setTablesWithGroupBy] = useState<Record<string, boolean>>({});
  const [queryLimit, setQueryLimit] = useState<number | undefined>(undefined);
  const [orderByPriority, setOrderByPriority] = useState<OrderByItem[]>([]);

  const { isOver, setNodeRef } = useDroppable({
    id: "studio-dropzone",
  });

  // Handle limit input change
  const handleLimitChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    // Allow empty input (no limit) or positive integers
    if (value === "") {
      setQueryLimit(undefined);
    } else {
      const numValue = parseInt(value, 10);
      if (!isNaN(numValue) && numValue > 0) {
        setQueryLimit(numValue);
      }
    }
  };

  const removeTable = useCallback(
    (tableId: string) => {
      // Also remove this table from the group by tracking
      setTablesWithGroupBy((prev) => {
        const updated = { ...prev };
        delete updated[tableId];

        // Calculate the updated state within this update function
        const updatedGroupByState = Object.values(updated).some(
          (hasGroupBy) => hasGroupBy
        );
        // Update within the same batch to avoid extra renders
        setAnyTableHasGroupBy(updatedGroupByState);

        return updated;
      });

      // Remove any order by items associated with this table
      setOrderByPriority((prev) =>
        prev.filter((item) => item.tableId !== tableId)
      );

      // Remove the table
      setDroppedTables((prevTables: TableItem[]) =>
        prevTables.filter((table: TableItem) => table.id !== tableId)
      );
    },
    [setDroppedTables, setOrderByPriority]
  );

  const handleGroupByChange = useCallback(
    (tableId: string, hasGroupBy: boolean) => {
      // Update the group by state for this specific table
      setTablesWithGroupBy((prev) => {
        const updated = { ...prev, [tableId]: hasGroupBy };

        // Check if any table has group by enabled within the same update
        const updatedGroupByState = Object.values(updated).some(
          (state) => state
        );

        // Update in the same batch
        setAnyTableHasGroupBy(updatedGroupByState);

        return updated;
      });
    },
    [setAnyTableHasGroupBy]
  );

  // Handle column changes from TableCustomizationPanel
  const handleColumnsChange = useCallback(
    (tableId: string, updatedColumns: Column[]) => {
      // Use functional update to ensure we're working with latest state
      setDroppedTables((prevTables) => {
        const currentTable = prevTables.find((table) => table.id === tableId);
        if (!currentTable) return prevTables;

        // Check if columns have actually changed
        const columnsEqual = areColumnsEqual(
          currentTable.customColumns,
          updatedColumns
        );
        if (columnsEqual) return prevTables;

        // Return new array with updated table
        return prevTables.map((table) =>
          table.id === tableId
            ? { ...table, customColumns: updatedColumns }
            : table
        );
      });
    },
    [] // No dependencies needed since we're using functional updates
  );

  // Helper function to compare column arrays
  const areColumnsEqual = (
    oldColumns: Column[] = [],
    newColumns: Column[] = []
  ): boolean => {
    if (oldColumns.length !== newColumns.length) return false;

    // Simple deep comparison of the columns
    return JSON.stringify(oldColumns) === JSON.stringify(newColumns);
  };

  // Create memoized callbacks for each table outside of the render method
  const tableCallbacks = useMemo(() => {
    return droppedTables.reduce(
      (acc, table) => {
        acc[table.id] = {
          onClose: () => removeTable(table.id),
          onGroupByChange: (hasGroupBy: boolean) =>
            handleGroupByChange(table.id, hasGroupBy),
          onColumnsChange: (columns: Column[]) =>
            handleColumnsChange(table.id, columns),
        };
        return acc;
      },
      {} as Record<
        string,
        {
          onClose: () => void;
          onGroupByChange: (hasGroupBy: boolean) => void;
          onColumnsChange: (columns: Column[]) => void;
        }
      >
    );
  }, [droppedTables, removeTable, handleGroupByChange, handleColumnsChange]);

  const handleRunVisualQuery = async () => {
    try {
      // Log the dropped tables for debugging
      console.log("Running visual query with tables:", droppedTables);
      console.log("Order by priority:", orderByPriority);

      // Map orderByPriority to the format expected by the service
      const orderByItems = orderByPriority.map((item) => ({
        tableId: item.tableId,
        tableName: item.tableName,
        columnName: item.columnName,
        direction: item.direction,
      }));

      const output = await runVisualQuery(
        droppedTables,
        queryLimit,
        orderByItems
      );
      if (!output || !output.table) {
        throw new Error("No output received from the query service");
      }

      setConsoleOutput(output.table);
      setQueryOutput(output.table.query);
    } catch (error: any) {
      setConsoleOutput({
        columns: [],
        rows: [],
        query: "",
      });

      setQueryOutput(
        `--Error: ${
          error.message || "An error occurred while running the query"
        }`
      );
    }
  };

  // Monitor order by selections across all tables
  useEffect(() => {
    // 1. Identify all currently active ORDER BY items from droppedTables
    const activeItemsMap: Record<string, OrderByItem> = {};
    droppedTables.forEach((table) => {
      if (!table.customColumns) return;
      table.customColumns.forEach((column) => {
        if (column.orderBy && column.orderBy !== "NONE") {
          const itemId = `${table.id}-${column.name}`;
          activeItemsMap[itemId] = {
            id: itemId,
            tableId: table.id,
            tableName: table.name,
            columnName: column.name,
            direction: column.orderBy,
          };
        }
      });
    });

    // 2. Filter the existing orderByPriority list, keeping only active items
    //    and updating their direction if needed.
    const preservedOrderItems = orderByPriority
      .filter((item) => activeItemsMap[item.id]) // Keep only items still active
      .map((item) => ({
        ...item,
        direction: activeItemsMap[item.id].direction, // Update direction if changed
      }));

    // 3. Identify items that are active but not in the preserved list (new items)
    const preservedIds = new Set(preservedOrderItems.map((item) => item.id));
    const newItems = Object.values(activeItemsMap).filter(
      (item) => !preservedIds.has(item.id)
    );

    // 4. Combine the preserved list and the new items
    const finalOrderByItems = [...preservedOrderItems, ...newItems];

    // 5. Compare and update state only if necessary
    const hasChanges =
      finalOrderByItems.length !== orderByPriority.length ||
      !orderByPriority.every(
        (item, index) =>
          finalOrderByItems[index] &&
          item.id === finalOrderByItems[index].id &&
          item.direction === finalOrderByItems[index].direction
      );

    if (hasChanges) {
      setOrderByPriority(finalOrderByItems);
    }
  }, [droppedTables, orderByPriority]);

  // Functions to handle reordering of the orderBy priority list
  const moveOrderByItemUp = (index: number) => {
    if (index <= 0) return; // Already at the top

    setOrderByPriority((prev) => {
      const newOrder = [...prev];
      // Swap with the item above
      [newOrder[index], newOrder[index - 1]] = [
        newOrder[index - 1],
        newOrder[index],
      ];
      return newOrder;
    });
  };

  const moveOrderByItemDown = (index: number) => {
    if (index >= orderByPriority.length - 1) return; // Already at the bottom

    setOrderByPriority((prev) => {
      const newOrder = [...prev];
      // Swap with the item below
      [newOrder[index], newOrder[index + 1]] = [
        newOrder[index + 1],
        newOrder[index],
      ];
      return newOrder;
    });
  };

  return (
    <div
      className="flex-1 p-6 h-full overflow-auto relative flex flex-col"
      style={{ zIndex: 1 }}
    >
      {/* Full-height container div to push the button to the bottom */}
      <div className="flex-1 flex flex-col">
        {/* Dropped tables display area */}
        {droppedTables.length > 0 && (
          <div className="mb-4">
            {droppedTables.map((table) => (
              <TableCustomizationPanel
                key={table.id}
                tableName={table.name}
                columns={table.columns}
                onClose={tableCallbacks[table.id].onClose}
                onGroupByChange={tableCallbacks[table.id].onGroupByChange}
                onColumnsChange={tableCallbacks[table.id].onColumnsChange}
                initialCustomColumns={table.customColumns}
                showAggregation={true}
                isAggregationEnabled={anyTableHasGroupBy}
              />
            ))}
          </div>
        )}

        {/* Display global state of group by - for debugging */}
        {droppedTables.length > 0 && (
          <div className="mb-4 px-2 py-1 glass rounded text-xs animate-slide-up">
            <p className="text-muted-foreground">
              {anyTableHasGroupBy
                ? "Aggregation functions available (Group By is active)"
                : "Add Group By to enable aggregation functions"}
            </p>
          </div>
        )}

        {/* Drag and drop area - takes up remaining space */}
        <div
          ref={setNodeRef}
          className={`flex-grow flex flex-col items-center justify-center p-4 border-2 ${
            isOver
              ? "border-primary border-dashed bg-primary/10 animate-glow"
              : "border-white/20 border-dashed"
          } rounded-lg transition-all-smooth glass`}
        >
          {isOver ? (
            <div className="text-center p-4">
              <p className="text-lg font-medium gradient-text animate-pulse-slow">
                Drop here to add to your query
              </p>
            </div>
          ) : (
            <div className="text-center p-4 w-full">
              <p className="mb-4 text-muted-foreground">
                {droppedTables.length === 0
                  ? "Build your query by dropping tables here"
                  : "Drop more tables to add to your query"}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Button Container - at the bottom */}
      <div className="flex justify-end mt-auto pt-4 items-center gap-2">
        {/* Order By Priority Panel */}
        {orderByPriority.length > 1 && (
          <div className="mr-auto">
            <div className="glass rounded-md p-2 max-w-md animate-float">
              <h4 className="text-xs font-medium mb-1 gradient-text">
                Order By Priority
              </h4>
              <div className="space-y-1">
                {orderByPriority.map((item, index) => (
                  <div
                    key={item.id}
                    className="flex items-center gap-1 glass rounded p-1 text-xs hover:bg-white/10 transition-all-smooth"
                  >
                    <span className="text-muted-foreground">{index + 1}.</span>
                    <span className="font-medium">
                      {item.tableName}.{item.columnName}
                    </span>
                    <span className="text-xs text-muted-foreground ml-1">
                      {item.direction === "ASC" ? "↑" : "↓"}
                    </span>
                    <div className="ml-auto flex">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => moveOrderByItemUp(index)}
                        disabled={index === 0}
                        className="h-5 w-5 p-0 hover:bg-white/10"
                        title="Move up in priority"
                      >
                        <ArrowUpIcon size={12} />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => moveOrderByItemDown(index)}
                        disabled={index === orderByPriority.length - 1}
                        className="h-5 w-5 p-0 hover:bg-white/10"
                        title="Move down in priority"
                      >
                        <ArrowDownIcon size={12} />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Use arrows to change priority (highest first)
              </p>
            </div>
          </div>
        )}
        <div className="flex items-center">
          <label
            htmlFor="query-limit"
            className="text-sm mr-2 text-muted-foreground"
          >
            Limit:
          </label>
          <input
            id="query-limit"
            type="number"
            min="1"
            className="w-20 px-2 py-1 text-sm glass-input rounded focus:outline-none focus:ring-1 focus:ring-primary transition-all-smooth"
            placeholder="None"
            value={queryLimit || ""}
            onChange={handleLimitChange}
            aria-label="Query result limit"
          />
        </div>
        <Button
          className="gradient-primary hover:shadow-lg hover:scale-105 transition-all-smooth cursor-pointer"
          onClick={handleRunVisualQuery}
        >
          Run Query
        </Button>
      </div>
    </div>
  );
}
