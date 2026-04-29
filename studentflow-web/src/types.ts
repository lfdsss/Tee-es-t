export type ContractType =
  | "internship"
  | "apprenticeship"
  | "cdd"
  | "cdi"
  | "part_time"
  | "freelance"
  | "other";

export type MatchState = "pending" | "accepted" | "declined";

export interface StudentCreate {
  email: string;
  full_name: string;
  city: string;
  remote_ok: boolean;
  skills: string[];
  accepted_contracts: ContractType[];
  max_hours_per_week: number;
  available_from?: string | null;
  available_until?: string | null;
  latitude?: number | null;
  longitude?: number | null;
}

export interface Match {
  offer_id: string;
  match_id?: string | null;
  title: string;
  company: string;
  city: string;
  url?: string;
  score: number;
  reasons: string[];
  distance_km?: number | null;
  state?: MatchState;
}

export interface StudentCreateResponse {
  id: string;
  completeness: number;
  matches: Match[];
}

export interface Stats {
  offers: number;
  students: number;
  matches: number;
  matches_unnotified: number;
  per_source: Record<string, number>;
}

export interface OfferCreate {
  title: string;
  company: string;
  description: string;
  city: string;
  remote: boolean;
  contract: ContractType;
  hours_per_week: number | null;
  skills: string[];
  url: string;
  contact_email: string;
  latitude?: number | null;
  longitude?: number | null;
}

export interface StudentMatch {
  student_id: string;
  full_name: string;
  email: string;
  city: string;
  skills: string[];
  score: number;
  reasons: string[];
  distance_km?: number | null;
}

export interface OfferCreateResponse {
  id: string;
  enriched_skills: string[];
  candidates: StudentMatch[];
}

export interface FunnelStats {
  offers: number;
  students: number;
  matches: {
    total: number;
    pending: number;
    accepted: number;
    declined: number;
  };
  acceptance_rate: number | null;
  decision_rate: number | null;
  per_source: Record<string, number>;
}
