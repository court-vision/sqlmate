import { TableApiService } from "./tableService";
import { QueryApiService } from "./queryService";

// Create and export singleton instances of each service
export const tableService = new TableApiService();
export const queryService = new QueryApiService();

// For direct import if needed
export { TableApiService, QueryApiService };
