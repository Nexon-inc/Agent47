/**
 * Admin API Client
 * Handles all communication with the backend admin API
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface AdminLoginRequest {
  email: string;
  password: string;
}

export interface AdminLoginResponse {
  access_token: string;
  token_type: string;
  admin_user: {
    user_id: string;
    email: string;
    permissions: string[];
  };
}

export interface AdminUser {
  user_id: string;
  email: string;
  permissions: string[];
  is_active: boolean;
  last_login?: string;
}

export interface PlatformConnection {
  id: number;
  platform: string;
  platform_display_name: string;
  account_name: string;
  account_handle?: string;
  status: string;
  is_active: boolean;
  last_used?: string;
  last_used_by_agent?: string;
  assigned_agents: Array<{
    agent_name: string;
    is_active: boolean;
    permissions: Record<string, boolean>;
    usage_count: number;
  }>;
  created_at: string;
}

class AdminAPI {
  private baseUrl: string;
  private token: string | null = null;

  constructor() {
    this.baseUrl = API_BASE_URL;
    // Load token from localStorage
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('admin_token');
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  // Authentication
  async login(email: string, password: string): Promise<AdminLoginResponse> {
    const formData = new URLSearchParams();
    formData.append('email', email);
    formData.append('password', password);

    // Build URL correctly - handle case where baseUrl might already include /api/v1
    let loginUrl: string;
    if (this.baseUrl.endsWith('/api/v1')) {
      loginUrl = `${this.baseUrl}/admin/login`;
    } else {
      loginUrl = `${this.baseUrl}/api/v1/admin/login`;
    }

    const response = await fetch(loginUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData.toString(),
    });

    if (!response.ok) {
      let errorMessage = 'Login failed'
      try {
        const error = await response.json()
        errorMessage = error.detail || error.message || error.error || 'Login failed'
      } catch {
        errorMessage = `HTTP ${response.status}: ${response.statusText}`
      }
      throw new Error(errorMessage)
    }

    const data = await response.json();
    this.token = data.access_token;
    
    if (typeof window !== 'undefined') {
      localStorage.setItem('admin_token', data.access_token);
    }

    return data;
  }

  async logout(): Promise<void> {
    try {
      await this.request('/admin/logout', { method: 'POST' });
    } finally {
      this.token = null;
      if (typeof window !== 'undefined') {
        localStorage.removeItem('admin_token');
      }
    }
  }

  async getCurrentAdmin(): Promise<AdminUser> {
    return this.request<AdminUser>('/admin/me');
  }

  // System Health
  async getHealth(): Promise<any> {
    return this.request('/admin/health');
  }

  async getMetrics(): Promise<any> {
    return this.request('/admin/metrics');
  }

  // Agents
  async getAgents(): Promise<any> {
    return this.request('/admin/agents');
  }

  async restartAgent(agentName: string): Promise<any> {
    return this.request(`/admin/agents/${agentName}/restart`, { method: 'POST' });
  }

  async getAgentLogs(agentName: string, lines: number = 100): Promise<any> {
    return this.request(`/admin/agents/${agentName}/logs?lines=${lines}`);
  }

  // Users
  async getUsers(page: number = 1, limit: number = 50): Promise<any> {
    return this.request(`/admin/users?page=${page}&limit=${limit}`);
  }

  async getUser(userId: string): Promise<any> {
    return this.request(`/admin/users/${userId}`);
  }

  async updateUserStatus(userId: string, isActive: boolean): Promise<any> {
    return this.request(`/admin/users/${userId}/status`, {
      method: 'PUT',
      body: JSON.stringify({ is_active: isActive }),
    });
  }

  // Database
  async getDatabaseStatus(): Promise<any> {
    return this.request('/admin/database/status');
  }

  async createDatabaseBackup(): Promise<any> {
    return this.request('/admin/database/backup', { method: 'POST' });
  }

  // Analytics
  async getAnalyticsOverview(): Promise<any> {
    return this.request('/admin/analytics/overview');
  }

  async getUserAnalytics(days: number = 30): Promise<any> {
    return this.request(`/admin/analytics/users?days=${days}`);
  }

  // System
  async getSystemStatus(): Promise<any> {
    return this.request('/admin/system/status');
  }

  async performSystemCleanup(): Promise<any> {
    return this.request('/admin/system/cleanup', { method: 'POST' });
  }

  // Security
  async getAuditLogs(page: number = 1, limit: number = 100): Promise<any> {
    return this.request(`/admin/security/audit-logs?page=${page}&limit=${limit}`);
  }

  async getSecurityThreats(): Promise<any> {
    return this.request('/admin/security/threats');
  }

  // Admin Users (Super Admin Only)
  async getAdminUsers(): Promise<any> {
    return this.request('/admin/admins');
  }

  async createAdminUser(
    email: string,
    userId: string,
    permissions: string[]
  ): Promise<any> {
    return this.request('/admin/admins/create', {
      method: 'POST',
      body: JSON.stringify({ email, user_id: userId, permissions }),
    });
  }

  async updateAdminPermissions(
    adminUserId: string,
    permissions: string[]
  ): Promise<any> {
    return this.request(`/admin/admins/${adminUserId}/permissions`, {
      method: 'PUT',
      body: JSON.stringify({ permissions }),
    });
  }

  async deactivateAdminUser(adminUserId: string): Promise<any> {
    return this.request(`/admin/admins/${adminUserId}`, {
      method: 'DELETE',
    });
  }

  // Platform Connections (Super Admin Only)
  async getAvailablePlatforms(): Promise<any> {
    return this.request('/admin/platforms/available');
  }

  async getPlatformConnections(activeOnly: boolean = true): Promise<any> {
    return this.request(`/admin/platforms/connections?active_only=${activeOnly}`);
  }

  async connectPlatform(
    platformName: string,
    accountName: string,
    accountHandle?: string,
    credentials?: any
  ): Promise<any> {
    return this.request('/admin/platforms/connect', {
      method: 'POST',
      body: JSON.stringify({
        platform_name: platformName,
        account_name: accountName,
        account_handle: accountHandle,
        credentials,
      }),
    });
  }

  async disconnectPlatform(credentialId: number): Promise<any> {
    return this.request(`/admin/platforms/${credentialId}/disconnect`, {
      method: 'POST',
    });
  }

  async getAgentPlatforms(agentName: string): Promise<any> {
    return this.request(`/admin/platforms/agents/${agentName}`);
  }

  async getAllAgentsPlatforms(): Promise<any> {
    return this.request('/admin/platforms/agents');
  }

  async assignAgentToPlatform(
    credentialId: number,
    agentName: string,
    permissions?: Record<string, boolean>,
    priority: number = 0
  ): Promise<any> {
    return this.request(`/admin/platforms/${credentialId}/assign-agent`, {
      method: 'POST',
      body: JSON.stringify({
        agent_name: agentName,
        permissions,
        priority,
      }),
    });
  }

  async removeAgentFromPlatform(
    credentialId: number,
    agentName: string
  ): Promise<any> {
    return this.request(`/admin/platforms/${credentialId}/agents/${agentName}`, {
      method: 'DELETE',
    });
  }

  async updateAgentPermissions(
    credentialId: number,
    agentName: string,
    permissions: Record<string, boolean>
  ): Promise<any> {
    return this.request(`/admin/platforms/${credentialId}/agents/${agentName}/permissions`, {
      method: 'PUT',
      body: JSON.stringify({ permissions }),
    });
  }

  async getPlatformStatistics(platformName?: string): Promise<any> {
    const url = platformName
      ? `/admin/platforms/statistics?platform_name=${platformName}`
      : '/admin/platforms/statistics';
    return this.request(url);
  }

  // Settings
  async getSettings(category?: string, publicOnly: boolean = false): Promise<any> {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    if (publicOnly) params.append('public_only', 'true');
    return this.request(`/admin/settings?${params.toString()}`);
  }

  async updateSetting(
    key: string,
    value: any,
    changeReason: string = ''
  ): Promise<any> {
    return this.request(`/admin/settings/${key}`, {
      method: 'PUT',
      body: JSON.stringify({ value, change_reason: changeReason }),
    });
  }

  // Logs
  async getLogs(filters: any, page: number = 1, limit: number = 100): Promise<any> {
    return this.request('/admin/logs', {
      method: 'POST',
      body: JSON.stringify({ filters, page, limit }),
    });
  }

  async getLogStatistics(startTime?: string, endTime?: string): Promise<any> {
    const params = new URLSearchParams();
    if (startTime) params.append('start_time', startTime);
    if (endTime) params.append('end_time', endTime);
    return this.request(`/admin/logs/statistics?${params.toString()}`);
  }

  // Feature Flags
  async getFeatureFlags(): Promise<any> {
    return this.request('/admin/feature-flags');
  }

  async createFeatureFlag(data: any): Promise<any> {
    return this.request('/admin/feature-flags', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateFeatureFlag(key: string, updates: any): Promise<any> {
    return this.request(`/admin/feature-flags/${key}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  // Cache
  async getCacheStatistics(cacheType?: string): Promise<any> {
    const url = cacheType
      ? `/admin/cache/statistics?cache_type=${cacheType}`
      : '/admin/cache/statistics';
    return this.request(url);
  }

  async clearCache(pattern?: string): Promise<any> {
    return this.request('/admin/cache/clear', {
      method: 'POST',
      body: JSON.stringify({ pattern }),
    });
  }

  // Alerts
  async getAlerts(severity?: string, status?: string, source?: string): Promise<any> {
    const params = new URLSearchParams();
    if (severity) params.append('severity', severity);
    if (status) params.append('status', status);
    if (source) params.append('source', source);
    const query = params.toString();
    return this.request(`/admin/alerts${query ? `?${query}` : ''}`);
  }

  async acknowledgeAlert(alertId: string): Promise<any> {
    return this.request(`/admin/alerts/${alertId}/acknowledge`, { method: 'POST' });
  }

  async resolveAlert(alertId: string): Promise<any> {
    return this.request(`/admin/alerts/${alertId}/resolve`, { method: 'POST' });
  }

  async getAlertStatistics(): Promise<any> {
    return this.request('/admin/alerts/statistics');
  }

  // Finance
  async getFinanceOverview(): Promise<any> {
    return this.request('/admin/finance/overview');
  }

  async getFinanceTransactions(page: number = 1, limit: number = 50): Promise<any> {
    return this.request(`/admin/finance/transactions?page=${page}&limit=${limit}`);
  }

  async getFinanceStatistics(): Promise<any> {
    return this.request('/admin/finance/statistics');
  }

  // Code
  async readCode(filePath: string): Promise<any> {
    return this.request('/admin/code/read', {
      method: 'POST',
      body: JSON.stringify({ file_path: filePath }),
    });
  }

  async writeCode(filePath: string, content: string): Promise<any> {
    return this.request('/admin/code/write', {
      method: 'POST',
      body: JSON.stringify({ file_path: filePath, content }),
    });
  }

  async executeCode(code: string, language?: string): Promise<any> {
    return this.request('/admin/code/execute', {
      method: 'POST',
      body: JSON.stringify({ code, language }),
    });
  }

  async getCodeHealth(): Promise<any> {
    return this.request('/admin/code/health');
  }

  // Terminal
  async createTerminalSession(): Promise<any> {
    return this.request('/admin/terminal/sessions', { method: 'POST' });
  }

  async executeTerminalCommand(sessionId: string, command: string): Promise<any> {
    return this.request(`/admin/terminal/sessions/${sessionId}/execute`, {
      method: 'POST',
      body: JSON.stringify({ command }),
    });
  }

  async getTerminalHistory(sessionId: string): Promise<any> {
    return this.request(`/admin/terminal/sessions/${sessionId}/history`);
  }

  async closeTerminalSession(sessionId: string): Promise<any> {
    return this.request(`/admin/terminal/sessions/${sessionId}`, { method: 'DELETE' });
  }

  // Communications
  async sendCommunication(
    recipients: string[],
    subject: string,
    message: string,
    communicationType?: string
  ): Promise<any> {
    return this.request('/admin/communications/send', {
      method: 'POST',
      body: JSON.stringify({
        recipients,
        subject,
        message,
        communication_type: communicationType || 'email',
      }),
    });
  }

  async getCommunicationStatus(communicationId: string): Promise<any> {
    return this.request(`/admin/communications/${communicationId}/status`);
  }

  async getCommunicationStatistics(): Promise<any> {
    return this.request('/admin/communications/statistics');
  }

  // Support
  async getSupportTickets(
    page: number = 1,
    limit: number = 50,
    status?: string,
    priority?: string
  ): Promise<any> {
    const params = new URLSearchParams();
    params.append('page', page.toString());
    params.append('limit', limit.toString());
    if (status) params.append('status', status);
    if (priority) params.append('priority', priority);
    return this.request(`/admin/support/tickets?${params.toString()}`);
  }

  async createSupportTicket(
    subject: string,
    description: string,
    priority: string,
    category?: string
  ): Promise<any> {
    return this.request('/admin/support/tickets', {
      method: 'POST',
      body: JSON.stringify({
        subject,
        description,
        priority,
        category: category || 'general',
      }),
    });
  }

  async updateTicketStatus(ticketId: string, status: string): Promise<any> {
    return this.request(`/admin/support/tickets/${ticketId}/status`, {
      method: 'PUT',
      body: JSON.stringify({ status }),
    });
  }

  async getSupportStatistics(): Promise<any> {
    return this.request('/admin/support/statistics');
  }

  // Servers
  async getServerStatus(): Promise<any> {
    return this.request('/admin/servers/status');
  }

  async getServerDetails(serverId: string): Promise<any> {
    return this.request(`/admin/servers/${serverId}`);
  }

  async getServerAlerts(): Promise<any> {
    return this.request('/admin/servers/alerts');
  }

  // Goals
  async getGoals(page: number = 1, limit: number = 50, status?: string): Promise<any> {
    const params = new URLSearchParams();
    params.append('page', page.toString());
    params.append('limit', limit.toString());
    if (status) params.append('status', status);
    return this.request(`/admin/goals?${params.toString()}`);
  }

  async createGoal(data: {
    name: string;
    description: string;
    priority: string;
    goal_type: string;
    assigned_agents: string[];
    target_date?: string;
  }): Promise<any> {
    return this.request('/admin/goals', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateGoal(goalId: string, updates: any): Promise<any> {
    return this.request(`/admin/goals/${goalId}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
  }

  async getGoalProgress(goalId: string): Promise<any> {
    return this.request(`/admin/goals/${goalId}/progress`);
  }

  // Impersonation
  async startImpersonation(userId: string, reason: string): Promise<any> {
    return this.request('/admin/impersonate/start', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, reason }),
    });
  }

  async endImpersonation(sessionId: string): Promise<any> {
    return this.request(`/admin/impersonate/${sessionId}/end`, { method: 'POST' });
  }

  async getImpersonationSession(sessionId: string): Promise<any> {
    return this.request(`/admin/impersonate/${sessionId}`);
  }

  async getImpersonationStatistics(): Promise<any> {
    return this.request('/admin/impersonate/statistics');
  }

  // Integrations
  async getIntegrationsOverview(): Promise<any> {
    return this.request('/admin/integrations/overview');
  }

  async getIntegrationDetails(integrationId: string): Promise<any> {
    return this.request(`/admin/integrations/${integrationId}`);
  }

  async getIntegrationStatistics(): Promise<any> {
    return this.request('/admin/integrations/statistics');
  }

  // Reports
  async getUsageReports(days: number = 30): Promise<any> {
    return this.request(`/admin/reports/usage?days=${days}`);
  }

  async getSubscriptionReports(days: number = 30): Promise<any> {
    return this.request(`/admin/reports/subscriptions?days=${days}`);
  }

  async getFinancialReports(days: number = 30): Promise<any> {
    return this.request(`/admin/reports/financial?days=${days}`);
  }

  async getRevenueForecast(months: number = 12): Promise<any> {
    return this.request(`/admin/reports/revenue-forecast?months=${months}`);
  }

  // Chat/Command Center
  async executeChatCommand(command: string, args?: string[]): Promise<any> {
    return this.request('/admin/chat/execute', {
      method: 'POST',
      body: JSON.stringify({ command, args: args || [] }),
    });
  }

  async getChatCommands(): Promise<any> {
    return this.request('/admin/chat/commands');
  }

  // Billing
  async getBillingSubscriptions(): Promise<any> {
    return this.request('/admin/billing/subscriptions');
  }

  async getBillingActivity(page: number = 1, limit: number = 50): Promise<any> {
    return this.request(`/admin/billing/activity?page=${page}&limit=${limit}`);
  }

  async getBillingAnalytics(): Promise<any> {
    return this.request('/admin/billing/analytics');
  }

  async getBillingRevenue(): Promise<any> {
    return this.request('/admin/billing/revenue');
  }
}

export const adminAPI = new AdminAPI();

