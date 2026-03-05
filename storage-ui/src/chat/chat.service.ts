import { Injectable, Logger } from '@nestjs/common';
import axios, { AxiosError } from 'axios';

export interface AgentResponse {
  response: string;
  session_id: string;
  status: string;
}

export interface HealthStatus {
  status: string;
  adk_available: boolean;
  project: string;
  credentials_file_exists: boolean;
  model: string;
}

@Injectable()
export class ChatService {
  private readonly logger = new Logger(ChatService.name);
  private readonly apiUrl: string;

  constructor() {
    this.apiUrl = process.env.AGENT_API_URL ?? 'http://localhost:8080';
    this.logger.log(`Agent backend: ${this.apiUrl}`);
  }

  async sendMessage(message: string, sessionId: string): Promise<string> {
    this.logger.log(`[${sessionId.slice(0, 8)}] → "${message.slice(0, 60)}"`);
    try {
      const { data } = await axios.post<AgentResponse>(
        `${this.apiUrl}/api/chat`,
        { message, session_id: sessionId },
        { timeout: 180_000 },  // 3 min — complex ops (backup, migration) take time
      );
      this.logger.log(`[${sessionId.slice(0, 8)}] ← ${data.response?.length ?? 0} chars`);
      return data.response ?? 'No response from agent.';
    } catch (err: unknown) {
      throw new Error(this.extractErrorMessage(err, '/api/chat'));
    }
  }

  async getHealth(): Promise<HealthStatus> {
    try {
      const { data } = await axios.get<HealthStatus>(
        `${this.apiUrl}/api/health`,
        { timeout: 5_000 },
      );
      return data;
    } catch (err: unknown) {
      throw new Error(this.extractErrorMessage(err, '/api/health'));
    }
  }

  async newSession(): Promise<string> {
    try {
      const { data } = await axios.post<{ session_id: string }>(
        `${this.apiUrl}/api/session/new`,
        {},
        { timeout: 5_000 },
      );
      return data.session_id;
    } catch (err: unknown) {
      throw new Error(this.extractErrorMessage(err, '/api/session/new'));
    }
  }

  private extractErrorMessage(err: unknown, endpoint: string): string {
    if (!err || typeof err !== 'object') {
      return `Unexpected error calling ${this.apiUrl}${endpoint}`;
    }
    const e = err as AxiosError<{ detail?: string; message?: string }>;
    const code = e.code;
    const status = e.response?.status;
    const detail = e.response?.data?.detail ?? e.response?.data?.message;

    this.logger.error(
      `Backend call failed [${endpoint}]: code=${code ?? 'none'} status=${status ?? 'none'} msg="${e.message ?? ''}"`,
    );

    if (code === 'ECONNREFUSED' || code === 'ENOTFOUND' || code === 'ECONNRESET') {
      return (
        `FastAPI backend is not reachable at ${this.apiUrl}.\n\n` +
        `Start it in a separate terminal:\n` +
        `  cd GCP-Cloudmate-ai\n` +
        `  uvicorn bucket_storage_agent.app:app --port 8080 --reload`
      );
    }
    if (code === 'ETIMEDOUT' || (e.message ?? '').toLowerCase().includes('timeout')) {
      return (
        `Request timed out after 3 minutes. ` +
        `Complex operations (backup, migration) may take longer — try a simpler request first.`
      );
    }
    if (status) {
      return detail
        ? `Backend error ${status}: ${detail}`
        : `Backend returned HTTP ${status}: ${e.message ?? 'unknown error'}`;
    }
    return e.message
      ? `${e.message} (calling ${this.apiUrl}${endpoint})`
      : `Unknown error calling ${this.apiUrl}${endpoint}`;
  }
}
