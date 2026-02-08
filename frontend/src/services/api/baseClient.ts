// Base API client with common functionality
export class BaseApiClient {
  protected baseUrl: string;
  private static tokenGetter: (() => Promise<string | null>) | null = null;

  constructor(baseUrl: string = "") {
    this.baseUrl = baseUrl;
  }

  // Set a token getter function (called once from a React component with Clerk's getToken)
  static setTokenGetter(getter: () => Promise<string | null>) {
    BaseApiClient.tokenGetter = getter;
  }

  // Get auth headers for protected endpoints
  protected async getAuthHeaders(): Promise<Record<string, string>> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    // First check sessionStorage for embedded mode token
    let token: string | null = null;
    if (typeof window !== "undefined") {
      token = sessionStorage.getItem("clerk-token");
    }

    // Fall back to Clerk token getter
    if (!token && BaseApiClient.tokenGetter) {
      token = await BaseApiClient.tokenGetter();
    }

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    return headers;
  }

  // Common GET request method
  protected async get<T>(
    endpoint: string,
    requiresAuth: boolean = true
  ): Promise<T> {
    const headers = requiresAuth
      ? await this.getAuthHeaders()
      : { "Content-Type": "application/json" };

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: "GET",
      headers,
      credentials: "include",
    });

    return this.handleResponse<T>(response);
  }

  // Common POST request method
  protected async post<T, U>(
    endpoint: string,
    data: T,
    requiresAuth: boolean = true
  ): Promise<U> {
    const headers = requiresAuth
      ? await this.getAuthHeaders()
      : { "Content-Type": "application/json" };

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: "POST",
      headers,
      credentials: "include",
      body: JSON.stringify(data),
    });

    return this.handleResponse<U>(response);
  }

  // Common DELETE request method
  protected async delete<T>(
    endpoint: string,
    requiresAuth: boolean = true
  ): Promise<T> {
    const headers = requiresAuth
      ? await this.getAuthHeaders()
      : { "Content-Type": "application/json" };

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: "DELETE",
      headers,
      credentials: "include",
    });

    return this.handleResponse<T>(response);
  }

  // Common response handler with proper error handling
  protected async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      if (!errorData || !errorData.details || !errorData.details.message) {
        throw new Error("Unknown error"); // Unknown error
      } else {
        // If errorData has a details field, use it
        throw new Error(errorData.details.message);
      }
    }

    return response.json();
  }
}
