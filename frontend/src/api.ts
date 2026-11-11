// api.ts - Klien API Terintegrasi UKK Assessment Platform
import type {
  User, Participant, RubricProfile, AssessmentSession,
  DashboardStats, AutoPlayConfig, AutoPlayLog, AWSCredentialInput
} from './types';

const API_BASE = import.meta.env.VITE_API_URL || '';

function getAuthHeader(): HeadersInit {
  const token = localStorage.getItem('ukk_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (res.status === 401) {
    localStorage.removeItem('ukk_token');
    localStorage.removeItem('ukk_user');
    window.location.reload();
    throw new Error('Sesi telah kedaluwarsa. Silakan login kembali.');
  }
  if (!res.ok) {
    let errMessage = `Error ${res.status}: ${res.statusText}`;
    try {
      const errJson = await res.json();
      if (errJson.detail) errMessage = errJson.detail;
    } catch {}
    throw new Error(errMessage);
  }
  return res.json();
}

export const api = {
  // Auth
  async login(formData: URLSearchParams): Promise<{ access_token: string; user: User }> {
    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData,
    });
    return handleResponse(res);
  },

  async getMe(): Promise<User> {
    const res = await fetch(`${API_BASE}/api/auth/me`, {
      headers: getAuthHeader(),
    });
    return handleResponse(res);
  },

  async changePassword(currentPassword: string, newPassword: string): Promise<any> {
    const res = await fetch(`${API_BASE}/api/auth/change-password`, {
      method: 'POST',
      headers: { ...getAuthHeader(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
    });
    return handleResponse(res);
  },

  // Dashboard
  async getDashboardStats(): Promise<DashboardStats> {
    const res = await fetch(`${API_BASE}/api/dashboard/stats`, {
      headers: getAuthHeader(),
    });
    return handleResponse(res);
  },

  // Participants
  async listParticipants(): Promise<Participant[]> {
    const res = await fetch(`${API_BASE}/api/participants`, {
      headers: getAuthHeader(),
    });
    return handleResponse(res);
  },

  async createParticipant(data: Omit<Participant, 'id' | 'created_at'>): Promise<Participant> {
    const res = await fetch(`${API_BASE}/api/participants`, {
      method: 'POST',
      headers: { ...getAuthHeader(), 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse(res);
  },

  async deleteParticipant(id: string): Promise<void> {
    const res = await fetch(`${API_BASE}/api/participants/${id}`, {
      method: 'DELETE',
      headers: getAuthHeader(),
    });
    return handleResponse(res);
  },

  // Rubrics
  async listRubrics(): Promise<RubricProfile[]> {
    const res = await fetch(`${API_BASE}/api/rubrics`, {
      headers: getAuthHeader(),
    });
    return handleResponse(res);
  },

  async getRubric(id: string): Promise<RubricProfile> {
    const res = await fetch(`${API_BASE}/api/rubrics/${id}`, {
      headers: getAuthHeader(),
    });
    return handleResponse(res);
  },

  async createRubric(data: any): Promise<RubricProfile> {
    const res = await fetch(`${API_BASE}/api/rubrics`, {
      method: 'POST',
      headers: { ...getAuthHeader(), 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse(res);
  },

  async updateRubric(id: string, data: any): Promise<RubricProfile> {
    const res = await fetch(`${API_BASE}/api/rubrics/${id}`, {
      method: 'PUT',
      headers: { ...getAuthHeader(), 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse(res);
  },

  async duplicateRubric(id: string): Promise<RubricProfile> {
    const res = await fetch(`${API_BASE}/api/rubrics/${id}/duplicate`, {
      method: 'POST',
      headers: getAuthHeader(),
    });
    return handleResponse(res);
  },

  async deleteRubric(id: string): Promise<void> {
    const res = await fetch(`${API_BASE}/api/rubrics/${id}`, {
      method: 'DELETE',
      headers: getAuthHeader(),
    });
    return handleResponse(res);
  },

  // Assessments
  async validateAWSCredentials(creds: AWSCredentialInput) {
    const res = await fetch(`${API_BASE}/api/assessments/validate-aws`, {
      method: 'POST',
      headers: { ...getAuthHeader(), 'Content-Type': 'application/json' },
      body: JSON.stringify(creds),
    });
    return handleResponse<any>(res);
  },

  async createAssessment(payload: {
    participant_id: string;
    rubric_profile_id: string;
    aws_credentials: AWSCredentialInput;
    notes?: string;
    run_app_tests: boolean;
  }): Promise<AssessmentSession> {
    const res = await fetch(`${API_BASE}/api/assessments`, {
      method: 'POST',
      headers: { ...getAuthHeader(), 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return handleResponse(res);
  },

  async reassess(assessmentId: string, creds: AWSCredentialInput, indicatorIds?: string[]) {
    const res = await fetch(`${API_BASE}/api/assessments/${assessmentId}/reassess`, {
      method: 'POST',
      headers: { ...getAuthHeader(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ aws_credentials: creds, indicator_ids: indicatorIds }),
    });
    return handleResponse<any>(res);
  },

  async getAiExplanation(assessmentId: string, indicatorId: string) {
    const res = await fetch(`${API_BASE}/api/assessments/${assessmentId}/indicators/${indicatorId}/ai-explain`, {
      method: 'POST',
      headers: getAuthHeader(),
    });
    return handleResponse<any>(res);
  },

  async listAssessments(): Promise<AssessmentSession[]> {
    const res = await fetch(`${API_BASE}/api/assessments`, {
      headers: getAuthHeader(),
    });
    return handleResponse(res);
  },

  async getAssessment(id: string): Promise<AssessmentSession> {
    const res = await fetch(`${API_BASE}/api/assessments/${id}`, {
      headers: getAuthHeader(),
    });
    return handleResponse(res);
  },

  // Auto Play
  async getAutoPlayConfig(): Promise<AutoPlayConfig> {
    const res = await fetch(`${API_BASE}/api/auto-play/config`, {
      headers: getAuthHeader(),
    });
    return handleResponse(res);
  },

  async updateAutoPlayConfig(data: { is_enabled: boolean; interval_minutes: number; target_instances?: any[] }): Promise<AutoPlayConfig> {
    const res = await fetch(`${API_BASE}/api/auto-play/config`, {
      method: 'PUT',
      headers: { ...getAuthHeader(), 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse(res);
  },

  async runAutoPlayNow(creds: AWSCredentialInput): Promise<any> {
    const res = await fetch(`${API_BASE}/api/auto-play/run-now`, {
      method: 'POST',
      headers: { ...getAuthHeader(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ credentials: creds }),
    });
    return handleResponse(res);
  },

  async getAutoPlayLogs(limit = 50): Promise<{ logs: AutoPlayLog[]; total: number }> {
    const res = await fetch(`${API_BASE}/api/auto-play/logs?limit=${limit}`, {
      headers: getAuthHeader(),
    });
    return handleResponse(res);
  },

  // Sheets
  async getSheetsStatus(): Promise<any> {
    const res = await fetch(`${API_BASE}/api/sheets/status`, {
      headers: getAuthHeader(),
    });
    return handleResponse(res);
  },

  async testSheetsConnection(): Promise<any> {
    const res = await fetch(`${API_BASE}/api/sheets/test`, {
      method: 'POST',
      headers: getAuthHeader(),
    });
    return handleResponse(res);
  },

  async configureSheets(jsonStr: string): Promise<any> {
    const res = await fetch(`${API_BASE}/api/sheets/configure`, {
      method: 'POST',
      headers: { ...getAuthHeader(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ service_account_json: jsonStr }),
    });
    return handleResponse(res);
  },

  async syncSheets(): Promise<any> {
    const res = await fetch(`${API_BASE}/api/sheets/sync`, {
      method: 'POST',
      headers: getAuthHeader(),
    });
    return handleResponse(res);
  },

  // Exporters URL
  getExportUrl(id: string, format: 'json' | 'csv' | 'html'): string {
    const token = localStorage.getItem('ukk_token') || '';
    return `${API_BASE}/api/assessments/${id}/export/${format}?token=${encodeURIComponent(token)}`;
  }
};
