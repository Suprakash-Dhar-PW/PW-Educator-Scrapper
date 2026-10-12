export interface SearchRequest {
  location: string;
  track: string;
  subject: string;
  force_refresh?: boolean;
  budget_max_anakin_searches?: number;
  budget_max_enrichments?: number;
  budget_max_candidates?: number;
  target_count?: number;
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
  full_name: string;
  professional_headline?: string;
  current_job_title?: string;
  current_employer?: string;
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
  pw_exclusion_status: string;
  identity_confidence: number;
  employment_verification_status: string;
  source_platform: string;
  profile_url: string;
}

export interface SearchResponse {
  query: Record<string, string>;
  total_results: number;
  target_count: number;
  target_reached: boolean;
  target_shortfall: number;
  unique_candidates_discovered: number;
  profiles_enriched: number;
  rejected_counts: Record<string, number>;
  review_queue_count: number;
  sources_searched: number;
  provider_errors: string[];
  search_duration_seconds: number;
  last_updated: string;
  credits_used: number;
  credits_estimated: number;
  cache_status: string;
  results: SearchResult[];
  review_results: SearchResult[];
}

const API_BASE = (import.meta as any).env?.VITE_API_BASE_URL || '/api';

export const apiClient = {
  getStates: async (): Promise<{code: string, name: string}[]> => {
    const res = await fetch(`${API_BASE}/locations/states`);
    if (!res.ok) throw new Error("Failed to load states");
    return res.json();
  },
  searchLocations: async (query: string, state_code?: string): Promise<{id: number, name: string, state_code: string, population: number}[]> => {
    const params = new URLSearchParams({ query });
    if (state_code) params.append("state_code", state_code);
    const res = await fetch(`${API_BASE}/locations/search?${params.toString()}`);
    if (!res.ok) throw new Error("Failed to search locations");
    return res.json();
  },
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
  },
  clearCache: async (): Promise<{status: string, message: string}> => {
    const res = await fetch(`${API_BASE}/cache/clear`, { method: "POST" });
    if (!res.ok) throw new Error("Failed to clear cache");
    return res.json();
  },
  getDiagnostics: async (): Promise<any> => {
    const res = await fetch(`${API_BASE}/diagnostics`);
    if (!res.ok) throw new Error("Failed to load diagnostics");
    return res.json();
  },
  getHealth: async (): Promise<any> => {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error("Failed to check health");
    return res.json();
  },
  getSavedEducators: async (): Promise<{ total: number, items: any[] }> => {
    const res = await fetch(`${API_BASE}/saved-educators`);
    if (!res.ok) throw new Error("Failed to load saved educators from Supabase");
    return res.json();
  },
  saveEducator: async (educator_id: string, notes: string = ""): Promise<any> => {
    const res = await fetch(`${API_BASE}/saved-educators/${educator_id}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ notes })
    });
    if (!res.ok) throw new Error(`Failed to save educator ${educator_id} to Supabase`);
    return res.json();
  },
  unsaveEducator: async (educator_id: string): Promise<{ status: string }> => {
    const res = await fetch(`${API_BASE}/saved-educators/${educator_id}`, {
      method: "DELETE"
    });
    if (!res.ok) throw new Error(`Failed to unsave educator ${educator_id} from Supabase`);
    return res.json();
  },
  recordExposure: async (educator_ids: string[], search_run_id?: string): Promise<void> => {
    if (!educator_ids.length) return;
    try {
      await fetch(`${API_BASE}/exposure`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ educator_ids, search_run_id })
      });
    } catch (e) {
      console.warn("Failed to record exposure history:", e);
    }
  }
};
