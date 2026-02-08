import type {
  QueryResponse,
  SaveTableRequest,
  SaveTableResponse,
  UpdateTableRequest,
  UpdateTableResponse,
  QueryRequest,
  Table,
  DeleteTableResponse,
} from "@/types/http";

const COMMON_OPTS = {
  headers: { "Content-Type": "application/json" },
  credentials: "include" as const,
};

// Helper function to get auth headers (async to support Clerk token)
const getAuthHeaders = async () => {
  let token: string | null = null;

  // Check sessionStorage for embedded mode token first
  if (typeof window !== "undefined") {
    token = sessionStorage.getItem("clerk-token");
  }

  // Fall back to Clerk token getter
  if (!token) {
    token = await getClerkToken();
  }

  return token
    ? {
        ...COMMON_OPTS.headers,
        Authorization: `Bearer ${token}`,
      }
    : COMMON_OPTS.headers;
};

// Module-level token getter that components can set
let clerkTokenGetter: (() => Promise<string | null>) | null = null;

export function setApiClientTokenGetter(getter: () => Promise<string | null>) {
  clerkTokenGetter = getter;
}

async function getClerkToken(): Promise<string | null> {
  if (clerkTokenGetter) {
    return clerkTokenGetter();
  }
  return null;
}

export async function getTableData(
  tableName: string
): Promise<Table | undefined> {
  const response = await fetch(
    `/users/get_table_data?table_name=${encodeURIComponent(tableName)}`,
    {
      method: "GET",
      headers: await getAuthHeaders(),
      credentials: "include",
    }
  );

  if (!response.ok) {
    throw new Error("Failed to fetch table data");
  }

  const data: QueryResponse = await response.json();
  return data.table;
}

export async function deleteUserTables(
  tableNames: string[]
): Promise<DeleteTableResponse> {
  const response = await fetch("/users/delete_table", {
    method: "POST",
    headers: await getAuthHeaders(),
    credentials: "include",
    body: JSON.stringify({ table_names: tableNames }),
  });
  if (!response.ok) {
    throw new Error("User table delete failed");
  }

  const data = await response.json();
  return data;
}

export async function getTables() {
  console.log("Fetching tables...");
  const response = await fetch("/users/get_tables", {
    method: "GET",
    headers: await getAuthHeaders(),
    credentials: "include",
  });
  if (!response.ok) {
    if (response.status === 404) {
      console.log("No tables found");
      return [];
    }
    throw new Error("Failed to fetch tables");
  }

  const data = await response.json();
  console.log("Tables fetched successfully:", data);
  return data;
}

export async function postUserTable(
  saveTableData: SaveTableRequest
): Promise<SaveTableResponse> {
  const response = await fetch("/users/save_table", {
    method: "POST",
    headers: await getAuthHeaders(),
    credentials: "include",
    body: JSON.stringify({
      table_name: saveTableData.table_name,
      query: saveTableData.query,
    }),
  });
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error_msg || "Table save failed");
  }
  const data: SaveTableResponse = await response.json();
  return data;
}

export async function postVisualQuery(
  queryData: QueryRequest
): Promise<QueryResponse> {
  const response = await fetch("/query", {
    method: "POST",
    headers: await getAuthHeaders(),
    credentials: "include",
    body: JSON.stringify(queryData),
  });
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error_msg || "Visual query failed");
  }
  const data: QueryResponse = await response.json();
  return data;
}

export async function postTableUpdate(
  updateData: UpdateTableRequest
): Promise<UpdateTableResponse> {
  const response = await fetch("/users/update_table", {
    method: "POST",
    headers: await getAuthHeaders(),
    credentials: "include",
    body: JSON.stringify(updateData),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error_msg || "Table update failed");
  }

  const data: UpdateTableResponse = await response.json();
  return data;
}

// Function to get table data for CSV export
export async function getTableDataForExport(
  tableName: string
): Promise<Table | undefined> {
  const response = await fetch(
    `/users/get_table_data?table_name=${encodeURIComponent(tableName)}`,
    {
      method: "GET",
      headers: await getAuthHeaders(),
      credentials: "include",
    }
  );
  if (!response.ok) {
    throw new Error("Failed to fetch table data for export");
  }

  const data: QueryResponse = await response.json();
  return data.table;
}
