export type CloudAiProviderName = 'huggingface' | 'openai' | 'gemini' | 'hybrid';

export type CloudAiAgentName =
  | 'scene_understanding'
  | 'object_metadata'
  | 'video_timeline_summary'
  | 'safety_review'
  | 'memory_query';

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

export interface CloudAiAgent {
  agent_name: CloudAiAgentName;
  display_name: string;
  description: string;
  best_for: string[];
}

export interface CloudAiHealth {
  status: string;
  default_provider: string;
  huggingface_enabled: boolean;
  openai_enabled: boolean;
  gemini_enabled: boolean;
  hybrid_order: string[];
}

export interface CloudAiConnectivity {
  provider: string;
  configured: boolean;
  connected: boolean;
  message: string;
  latency_ms: number | null;
}

export interface CloudAiProviderResult {
  provider: string;
  model: string;
  agent_name: string;
  prompt: string;
  output_text: string;
  parsed_json: Record<string, unknown> | null;
  raw_response: Record<string, unknown> | null;
}

export interface CloudAiImageAnalysisResult {
  original_filename: string;
  provider_result: CloudAiProviderResult;
}

export interface CloudAiTextSummaryResult {
  provider_result: CloudAiProviderResult;
}
