"use client";
import { useState } from "react";
import type { Table } from "@/types/http";
import { Header } from "@/components/header";
import { TablePanel } from "@/components/tablePanel";
import { StudioCanvas } from "@/components/studioCanvas";
import { ConsolePanel } from "@/components/consolePanel";
import {
  ResizablePanelGroup,
  ResizablePanel,
  ResizableHandle,
} from "@/components/ui/resizable";
import {
  DndContext,
  DragEndEvent,
  DragOverlay,
  DragStartEvent,
} from "@dnd-kit/core";
import { TableItem } from "@/components/tablePanel";
import { Card } from "@/components/ui/card";

export default function Home() {
  const [consoleOutput, setConsoleOutput] = useState<Table | null>(null);
  const [queryOutput, setQueryOutput] = useState<string | null>(null);
  const [droppedTables, setDroppedTables] = useState<TableItem[]>([]);
  const [activeTable, setActiveTable] = useState<TableItem | null>(null);

  const handleDragStart = (event: DragStartEvent) => {
    // Set the active table data for the overlay
    if (event.active.data.current) {
      setActiveTable(event.active.data.current as TableItem);
    }
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    // Reset active table
    setActiveTable(null);

    if (over && over.id === "studio-dropzone") {
      // Get the table data from the dragged item
      const tableData = active.data.current as TableItem;

      // Check if table already exists in droppedTables
      const tableExists = droppedTables.some(
        (table) => table.id === tableData.id
      );

      if (!tableExists) {
        setDroppedTables((prev) => [...prev, tableData]);
      }
    }
  };

  // Drag overlay table preview component
  const DragPreview = ({ table }: { table: TableItem }) => {
    return (
      <Card className="p-3 glass shadow-lg border-2 border-primary/50 w-64 animate-glow">
        <div className="font-medium text-sm gradient-text">{table.name}</div>
        <div className="mt-2 text-xs text-muted-foreground">
          {table.columns.length} columns
        </div>
      </Card>
    );
  };

  return (
    <DndContext onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
      <div className="flex flex-col h-screen w-full relative overflow-hidden">
        {/* Animated background particles */}
        <div className="absolute inset-0 opacity-30">
          <div className="absolute top-1/4 left-1/4 w-2 h-2 bg-blue-400 rounded-full animate-pulse-slow"></div>
          <div
            className="absolute top-3/4 right-1/4 w-1 h-1 bg-purple-400 rounded-full animate-pulse-slow"
            style={{ animationDelay: "1s" }}
          ></div>
          <div
            className="absolute top-1/2 left-3/4 w-1.5 h-1.5 bg-cyan-400 rounded-full animate-pulse-slow"
            style={{ animationDelay: "2s" }}
          ></div>
          <div
            className="absolute top-1/6 right-1/3 w-1 h-1 bg-pink-400 rounded-full animate-pulse-slow"
            style={{ animationDelay: "0.5s" }}
          ></div>
        </div>

        <Header />
        <div className="flex h-full relative z-10">
          <TablePanel />
          <ResizablePanelGroup direction="horizontal" className="flex-1">
            <ResizablePanel>
              <StudioCanvas
                setConsoleOutput={setConsoleOutput}
                setQueryOutput={setQueryOutput}
                droppedTables={droppedTables}
                setDroppedTables={setDroppedTables}
              />
            </ResizablePanel>
            <ResizableHandle
              withHandle
              className="bg-border hover:bg-accent transition-all-smooth"
            />
            <ResizablePanel defaultSize={30} minSize={10}>
              <ConsolePanel
                consoleOutput={consoleOutput}
                queryOutput={queryOutput}
              />
            </ResizablePanel>
          </ResizablePanelGroup>
        </div>

        {/* Drag overlay for table preview */}
        <DragOverlay dropAnimation={null}>
          {activeTable ? <DragPreview table={activeTable} /> : null}
        </DragOverlay>
      </div>
    </DndContext>
  );
}
