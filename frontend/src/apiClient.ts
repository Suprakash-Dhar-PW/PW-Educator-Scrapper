export interface SearchRequest {
  location: string;
  track: string;
  subject: string;
  force_refresh?: boolean;
}

export interface PlatformProfile {
  platform: string;
  url: string;
  name?: string;
  username?: string;
  followers?: number;
  subscribers?: number;
  connections?: number;
}

export interface Evidence {
  dimension: string;
  platform: string;
  text: string;
}

export interface SearchResult {
  educator_id: string;
  name: string;
  location: string;
  track: string;
  subjects: string[];
  profiles: PlatformProfile[];
  scores: {
    overall: number;
    components: Record<string, number>;
    reasons: string[];
  };
  evidence: Evidence[];
}

export interface SearchResponse {
  query: Record<string, string>;
  total_results: number;
  last_updated: string;
  results: SearchResult[];
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

export const apiClient = {
  getLocations: async (): Promise<string[]> => {
    const res = await fetch(`${API_BASE}/locations`);
    if (!res.ok) throw new Error("Failed to load locations");
    return res.json();
  },
  getTracks: async (): Promise<string[]> => {
    const res = await fetch(`${API_BASE}/tracks`);
    if (!res.ok) throw new Error("Failed to load tracks");
    return res.json();
  },
  getSubjects: async (track: string): Promise<string[]> => {
    const res = await fetch(`${API_BASE}/subjects?track=${encodeURIComponent(track)}`);
    if (!res.ok) throw new Error("Failed to load subjects");
    return res.json();
  },
  search: async (req: SearchRequest): Promise<SearchResponse> => {
    const res = await fetch(`${API_BASE}/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req)
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => null);
      throw new Error(errorData?.detail || "Search failed");
    }
    return res.json();
  }
}
