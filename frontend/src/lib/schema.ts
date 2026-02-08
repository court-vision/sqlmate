import { TableItem } from "@/components/tablePanel";

interface SchemaTable {
  table: string;
  columns: Array<{
    name: string;
    type: string;
  }>;
}

let cachedSchema: TableItem[] | null = null;

// Function to load database schema from the backend /schema endpoint
export async function loadDatabaseSchema(): Promise<TableItem[]> {
  if (cachedSchema) {
    return cachedSchema;
  }

  try {
    const response = await fetch("/schema");
    if (!response.ok) {
      throw new Error(`Failed to fetch schema: ${response.status}`);
    }

    const data: SchemaTable[] = await response.json();
    cachedSchema = data.map((table) => ({
      id: `${table.table}-table`,
      name: table.table,
      columns: table.columns.map((col) => ({
        name: col.name,
        type: col.type,
      })),
    }));

    return cachedSchema;
  } catch (error) {
    console.error("Error loading database schema:", error);
    return [];
  }
}
