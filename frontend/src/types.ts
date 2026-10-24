export type AudioItem = {
  id: string;
  name: string;
  duration: number;
  sample_rate: number;
  channels: number;
  size: number;
};
export type VoiceModel = {
  id: string;
  name: string;
  version: string;
  sample_rate: number;
  speakers: number;
  pitch_guidance: boolean;
  size: number;
  index_path: string | null;
  origin: string;
};
export type Project = { id: string; name: string; audio_ids: string[] };
export type Output = {
  name: string;
  path: string;
  kind: string;
  audio_id?: string;
};
export type Job = {
  id: string;
  kind: "setup" | "conversion" | "training";
  title: string;
  status:
    "queued" | "running" | "completed" | "failed" | "cancelled" | "interrupted";
  phase: string;
  progress: number;
  error: string | null;
  outputs: Output[];
  created_at: string;
  model_id?: string;
  can_resume?: boolean;
  parameters: Record<string, unknown>;
};
export type SystemInfo = {
  gpu: {
    name: string;
    device: string;
    backend?: string;
    memory_gb?: number;
    error?: string;
    note?: string;
    torch: string;
  };
  assets: { name: string; ready: boolean; size: number }[];
  disk_free_gb: number;
  version: string;
};
export type Library = {
  audio: AudioItem[];
  models: VoiceModel[];
  projects: Project[];
  jobs: Job[];
};
export type Notify = (message: string, error?: boolean) => void;
export type Page = "studio" | "models" | "training" | "results" | "system";
