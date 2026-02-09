import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useDraggable } from "@dnd-kit/core";
import { loadDatabaseSchema } from "@/lib/schema";
import { Column } from "./tableCustomizationPanel";

interface TableColumn {
  name: string;
  type: string;
}

interface TableData {
  name: string;
  columns: TableColumn[];
}

export interface TableItem extends TableData {
  id: string;
  customColumns?: Column[]; // Add customColumns property to store customizations
}

// Will be populated from the JSON file
export let dbTables: TableItem[] = [];

function DraggableTableItem({
  table,
  isPanelExpanded,
}: {
  table: TableItem;
  isPanelExpanded: boolean;
}) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: table.id,
    data: table,
  });

  return (
    <Card
      ref={setNodeRef}
      style={{
        opacity: isDragging ? 0.3 : 1, // Make it partially transparent when dragging
        cursor: "grab",
        // Note: we're not transforming the original element anymore,
        // that's handled by the DragOverlay instead
      }}
      className={`cursor-grab active:cursor-grabbing p-3 glass hover:bg-accent hover-lift transition-all-smooth ${
        isDragging ? "ring-2 ring-primary animate-glow" : ""
      }`}
      {...listeners}
      {...attributes}
    >
      <div className="font-medium text-sm gradient-text">
        {isPanelExpanded ? table.name : table.name.substring(0, 1)}
      </div>
      {isPanelExpanded && (
        <div className="mt-2 text-xs text-muted-foreground">
          {table.columns.length} columns
        </div>
      )}
    </Card>
  );
}

export function TablePanel() {
  const [isPanelExpanded, setIsPanelExpanded] = useState(true);
  const [tables, setTables] = useState<TableItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Load schema when component mounts
  useEffect(() => {
    async function fetchSchema() {
      setIsLoading(true);
      try {
        const schema = await loadDatabaseSchema();
        setTables(schema);
        // Update exported variable for other components to use
        dbTables = schema;
      } catch (error) {
        console.error("Failed to load schema:", error);
      } finally {
        setIsLoading(false);
      }
    }

    fetchSchema();
  }, []);

  return (
    <div
      className={`glass border-r border-border transition-all duration-200 flex flex-col ${
        isPanelExpanded ? "w-64" : "w-16"
      }`}
      style={{ zIndex: 10 }} // Ensure the panel has a reasonable z-index
    >
      <div className="p-4 border-b border-border flex justify-between items-center">
        <h2
          className={`font-medium gradient-text ${
            isPanelExpanded ? "block" : "hidden"
          }`}
        >
          Tables
        </h2>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setIsPanelExpanded(!isPanelExpanded)}
          className="h-8 w-8 hover:bg-accent transition-all-smooth"
        >
          {isPanelExpanded ? "←" : "→"}
        </Button>
      </div>
      <div className="overflow-y-auto p-3 flex flex-col gap-2 flex-1">
        {isLoading ? (
          <div className="text-center p-4 text-sm text-muted-foreground">
            <div className="spinner-gradient w-6 h-6 mx-auto mb-2"></div>
            Loading tables...
          </div>
        ) : tables.length === 0 ? (
          <div className="text-center p-4 text-sm text-muted-foreground">
            No tables found.
          </div>
        ) : (
          tables.map((table) => (
            <DraggableTableItem
              key={table.id}
              table={table}
              isPanelExpanded={isPanelExpanded}
            />
          ))
        )}
      </div>
    </div>
  );
}
