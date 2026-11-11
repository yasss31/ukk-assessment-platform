// types.ts - Definisi Tipe Frontend UKK Assessment Platform

export interface User {
  id: string;
  username: string;
  full_name: string;
  role: 'super_admin' | 'examiner';
  email?: string;
  is_active: boolean;
  created_at: string;
}

export interface Participant {
  id: string;
  name: string;
  participant_number: string;
  student_class: string;
  school: string;
  created_at?: string;
}

export interface RubricIndicator {
  id: string;
  code: string;
  name: string;
  category: string;
  expected_value: string;
  weight: number;
  check_method: string;
  description?: string;
  is_active: boolean;
}

export interface RubricProfile {
  id: string;
  name: string;
  version: string;
  description: string;
  indicators: RubricIndicator[];
  total_weight: number;
  created_at: string;
  updated_at: string;
}

export interface AWSCredentialInput {
  aws_access_key_id: string;
  aws_secret_access_key: string;
  aws_session_token: string;
  aws_region: string;
}

export interface IndicatorResult {
  indicator_id: string;
  code: string;
  name: string;
  category: string;
  expected: string;
  actual: string;
  status: 'PASS' | 'FAIL' | 'SKIP' | 'ERROR' | 'WARNING';
  score: number;
  weight: number;
  evidence: string;
  error_message?: string;
  timestamp?: string;
}

export interface AssessmentSession {
  id: string;
  participant: Participant;
  rubric_id: string;
  rubric_name: string;
  rubric_version: string;
  examiner_name: string;
  aws_account_id?: string;
  aws_region: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
  total_score: number;
  max_score: number;
  pass_count: number;
  fail_count: number;
  skip_count: number;
  error_count: number;
  warning_count: number;
  completion_percentage: number;
  results: IndicatorResult[];
  notes?: string;
  started_at: string;
  completed_at?: string;
  duration_seconds?: number;
}

export interface DashboardStats {
  total_assessments: number;
  completed_assessments: number;
  average_score: number;
  pass_rate: number;
  total_participants: number;
  active_rubrics_count: number;
  google_sheets: {
    is_connected: boolean;
    status: string;
    spreadsheet_id: string;
    error?: string;
  };
  auto_play: {
    is_enabled: boolean;
    interval_minutes: number;
    last_status: string;
    next_run?: string;
  };
  recent_assessments: AssessmentSession[];
}

export interface AutoPlayConfig {
  is_enabled: boolean;
  interval_minutes: number;
  max_retries: number;
  target_instances: any[];
  last_run?: string;
  next_run?: string;
  last_status: string;
  last_error?: string;
}

export interface AutoPlayLog {
  id: string;
  timestamp: string;
  action: string;
  status: string;
  account_id?: string;
  target_instance_id?: string;
  details: string;
}
