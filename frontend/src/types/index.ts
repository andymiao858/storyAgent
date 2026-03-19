export interface ApiResponse<T = unknown> {
  code: number;
  message: string;
  data: T;
}

export interface User {
  id: number;
  email: string;
  role: string;
}

export interface AuthData {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Child {
  id: number;
  parent_id: number;
  nickname: string;
  age: number;
  avatar_url: string;
  interests: string[];
  reading_level: string;
  is_active: boolean;
}

export interface ParentSettings {
  id: number;
  parent_id: number;
  blocked_topics: string[];
  preferred_themes: string[];
  daily_limit_minutes: number;
}

export interface StoryStartResponse {
  story_id: number;
  session_id: number;
  title: string;
  first_scene_text: string;
  options: StoryOption[];
  is_finished: boolean;
}

export interface StoryContinueResponse {
  next_scene_text: string;
  options: StoryOption[];
  is_finished: boolean;
  summary?: string;
  parent_suggestion?: string;
}

export interface StoryOption {
  key: string;
  text: string;
}

export interface StoryHistoryItem {
  id: number;
  title: string;
  theme: string;
  main_character: string;
  scene: string;
  story_status: string;
  session_id: number | null;
  created_at: string;
}

export interface GrowthReport {
  id: number;
  child_id: number;
  report_date: string;
  summary: string;
  behavior_tags: string[];
  recommendations: string;
}
