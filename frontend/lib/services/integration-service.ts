import { apiClient } from '../api-client';

export interface IntegrationConfig {
  name: string;
  display_name: string;
  integration_type: string;
  description: string;
  provider: string;
  api_version: string;
  pricing_tier: string;
  rate_limits: {
    requests_per_minute: number;
    requests_per_hour: number;
    requests_per_day: number;
  };
  supported_features: {
    api_access: boolean;
    webhooks: boolean;
    real_time: boolean;
    bulk_operations: boolean;
    [key: string]: boolean;
  };
  authentication_methods: {
    oauth2: boolean;
    api_key: boolean;
    bearer_token: boolean;
  };
  scopes: string[];
  supports_oauth: boolean;
  supports_api_key: boolean;
  supports_bearer_token: boolean;
}

export interface ConnectedIntegration {
  id: number;
  integration_name: string;
  integration_display_name: string;
  integration_type: string;
  scopes: string[];
  status: 'valid' | 'expired' | 'invalid' | 'revoked';
  expires_at?: string;
  last_used?: string;
  created_at: string;
  last_updated?: string;
}

export interface IntegrationCredentials {
  api_key?: string;
  api_secret?: string;
  access_token?: string;
  refresh_token?: string;
  bearer_token?: string;
  scopes?: string[];
}

export interface OAuthInitiationResult {
  success: boolean;
  oauth_url?: string;
  integration?: string;
  scopes?: string[];
  state?: string;
  error?: string;
}

export interface IntegrationAuditLog {
  id: number;
  user_id: number;
  integration_name: string;
  action: string;
  severity: string;
  request_id?: string;
  agent_name?: string;
  ip_address?: string;
  user_agent?: string;
  description: string;
  metadata: Record<string, any>;
  scopes_used: string[];
  success: string;
  error_message?: string;
  response_code?: number;
  duration_ms?: number;
  timestamp: string;
}

export class IntegrationService {
  private static instance: IntegrationService;
  private baseUrl: string;

  private constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  }

  public static getInstance(): IntegrationService {
    if (!IntegrationService.instance) {
      IntegrationService.instance = new IntegrationService();
    }
    return IntegrationService.instance;
  }

  /**
   * Get all available integrations
   */
  async getAvailableIntegrations(integrationType?: string): Promise<IntegrationConfig[]> {
    try {
      const params = integrationType ? `?integration_type=${integrationType}` : '';
      const response = await apiClient.get(`/integrations/available${params}`);
      
      if (response.success) {
        return response.integrations;
      } else {
        throw new Error('Failed to get available integrations');
      }
    } catch (error) {
      console.error('Error getting available integrations:', error);
      throw error;
    }
  }

  /**
   * Connect to an integration using credentials
   */
  async connectIntegration(
    integrationName: string, 
    credentials: IntegrationCredentials
  ): Promise<{ success: boolean; message?: string; error?: string }> {
    try {
      const response = await apiClient.post(`/integrations/connect/${integrationName}`, credentials);
      
      if (response.success) {
        return {
          success: true,
          message: response.message
        };
      } else {
        return {
          success: false,
          error: response.error || 'Failed to connect integration'
        };
      }
    } catch (error: any) {
      console.error('Error connecting integration:', error);
      return {
        success: false,
        error: error.message || 'Failed to connect integration'
      };
    }
  }

  /**
   * Initiate OAuth connection to an integration
   */
  async initiateOAuthConnection(integrationName: string): Promise<OAuthInitiationResult> {
    try {
      const response = await apiClient.get(`/integrations/oauth/${integrationName}`);
      
      if (response.success) {
        return {
          success: true,
          oauth_url: response.oauth_url,
          integration: response.integration,
          scopes: response.scopes,
          state: response.state
        };
      } else {
        return {
          success: false,
          error: response.error || 'Failed to initiate OAuth connection'
        };
      }
    } catch (error: any) {
      console.error('Error initiating OAuth connection:', error);
      return {
        success: false,
        error: error.message || 'Failed to initiate OAuth connection'
      };
    }
  }

  /**
   * Get user's connected integrations
   */
  async getConnectedIntegrations(): Promise<ConnectedIntegration[]> {
    try {
      const response = await apiClient.get('/integrations/connected');
      
      if (response.success) {
        return response.integrations;
      } else {
        throw new Error('Failed to get connected integrations');
      }
    } catch (error) {
      console.error('Error getting connected integrations:', error);
      throw error;
    }
  }

  /**
   * Disconnect from an integration
   */
  async disconnectIntegration(integrationName: string): Promise<{ success: boolean; message?: string; error?: string }> {
    try {
      const response = await apiClient.post(`/integrations/disconnect/${integrationName}`);
      
      if (response.success) {
        return {
          success: true,
          message: response.message
        };
      } else {
        return {
          success: false,
          error: response.error || 'Failed to disconnect integration'
        };
      }
    } catch (error: any) {
      console.error('Error disconnecting integration:', error);
      return {
        success: false,
        error: error.message || 'Failed to disconnect integration'
      };
    }
  }

  /**
   * Refresh integration credentials
   */
  async refreshCredentials(integrationName: string): Promise<{ success: boolean; message?: string; error?: string }> {
    try {
      const response = await apiClient.post(`/integrations/refresh/${integrationName}`);
      
      if (response.success) {
        return {
          success: true,
          message: response.message
        };
      } else {
        return {
          success: false,
          error: response.error || 'Failed to refresh credentials'
        };
      }
    } catch (error: any) {
      console.error('Error refreshing credentials:', error);
      return {
        success: false,
        error: error.message || 'Failed to refresh credentials'
      };
    }
  }

  /**
   * Validate integration access
   */
  async validateAccess(integrationName: string, scopes?: string[]): Promise<{ success: boolean; has_access?: boolean; error?: string }> {
    try {
      const params = scopes ? `?scopes=${scopes.join(',')}` : '';
      const response = await apiClient.get(`/integrations/validate/${integrationName}${params}`);
      
      if (response.success) {
        return {
          success: true,
          has_access: response.has_access
        };
      } else {
        return {
          success: false,
          error: response.error || 'Failed to validate access'
        };
      }
    } catch (error: any) {
      console.error('Error validating integration access:', error);
      return {
        success: false,
        error: error.message || 'Failed to validate access'
      };
    }
  }

  /**
   * Get integration audit logs
   */
  async getAuditLogs(
    integrationName?: string,
    action?: string,
    limit: number = 100,
    offset: number = 0
  ): Promise<IntegrationAuditLog[]> {
    try {
      const params = new URLSearchParams();
      if (integrationName) params.append('integration_name', integrationName);
      if (action) params.append('action', action);
      params.append('limit', limit.toString());
      params.append('offset', offset.toString());
      
      const response = await apiClient.get(`/integrations/audit-logs?${params.toString()}`);
      
      if (response.success) {
        return response.logs;
      } else {
        throw new Error('Failed to get audit logs');
      }
    } catch (error) {
      console.error('Error getting audit logs:', error);
      throw error;
    }
  }

  /**
   * Redirect to integration OAuth URL
   */
  redirectToOAuth(oauthUrl: string): void {
    if (typeof window !== 'undefined') {
      window.location.href = oauthUrl;
    }
  }

  /**
   * Get integration icon and styling
   */
  getIntegrationInfo(integrationName: string): { icon: string; color: string; bgColor: string } {
    const integrationInfo: Record<string, { icon: string; color: string; bgColor: string }> = {
      mailchimp: {
        icon: 'mail',
        color: 'text-yellow-600',
        bgColor: 'bg-yellow-600'
      },
      convertkit: {
        icon: 'users',
        color: 'text-orange-600',
        bgColor: 'bg-orange-600'
      },
      klaviyo: {
        icon: 'bar-chart',
        color: 'text-purple-600',
        bgColor: 'bg-purple-600'
      },
      google_analytics: {
        icon: 'bar-chart',
        color: 'text-blue-600',
        bgColor: 'bg-blue-600'
      },
      mixpanel: {
        icon: 'activity',
        color: 'text-green-600',
        bgColor: 'bg-green-600'
      },
      amplitude: {
        icon: 'trending-up',
        color: 'text-indigo-600',
        bgColor: 'bg-indigo-600'
      },
      hubspot: {
        icon: 'building',
        color: 'text-orange-500',
        bgColor: 'bg-orange-500'
      },
      salesforce: {
        icon: 'cloud',
        color: 'text-blue-500',
        bgColor: 'bg-blue-500'
      },
      pipedrive: {
        icon: 'trending-up',
        color: 'text-green-500',
        bgColor: 'bg-green-500'
      },
      wordpress: {
        icon: 'globe',
        color: 'text-blue-700',
        bgColor: 'bg-blue-700'
      },
      contentful: {
        icon: 'layers',
        color: 'text-purple-500',
        bgColor: 'bg-purple-500'
      },
      notion: {
        icon: 'file-text',
        color: 'text-gray-600',
        bgColor: 'bg-gray-600'
      },
      figma: {
        icon: 'palette',
        color: 'text-pink-500',
        bgColor: 'bg-pink-500'
      },
      canva: {
        icon: 'image',
        color: 'text-blue-400',
        bgColor: 'bg-blue-400'
      },
      slack: {
        icon: 'message-square',
        color: 'text-purple-600',
        bgColor: 'bg-purple-600'
      },
      trello: {
        icon: 'columns',
        color: 'text-blue-600',
        bgColor: 'bg-blue-600'
      },
      asana: {
        icon: 'check-square',
        color: 'text-red-500',
        bgColor: 'bg-red-500'
      },
      stripe: {
        icon: 'credit-card',
        color: 'text-indigo-600',
        bgColor: 'bg-indigo-600'
      },
      paypal: {
        icon: 'dollar-sign',
        color: 'text-blue-600',
        bgColor: 'bg-blue-600'
      },
      openai: {
        icon: 'brain',
        color: 'text-green-600',
        bgColor: 'bg-green-600'
      },
      'chutes-ai': {
        icon: 'zap',
        color: 'text-yellow-500',
        bgColor: 'bg-yellow-500'
      },
      'grok-llm': {
        icon: 'cpu',
        color: 'text-gray-700',
        bgColor: 'bg-gray-700'
      },
      zapier: {
        icon: 'link',
        color: 'text-orange-500',
        bgColor: 'bg-orange-500'
      },
      ifttt: {
        icon: 'settings',
        color: 'text-red-500',
        bgColor: 'bg-red-500'
      }
    };

    return integrationInfo[integrationName] || {
      icon: 'puzzle',
      color: 'text-gray-600',
      bgColor: 'bg-gray-600'
    };
  }

  /**
   * Get integration type color
   */
  getIntegrationTypeColor(integrationType: string): string {
    const typeColors: Record<string, string> = {
      marketing: 'bg-pink-100 text-pink-800',
      analytics: 'bg-blue-100 text-blue-800',
      crm: 'bg-green-100 text-green-800',
      content: 'bg-purple-100 text-purple-800',
      design: 'bg-yellow-100 text-yellow-800',
      productivity: 'bg-indigo-100 text-indigo-800',
      finance: 'bg-emerald-100 text-emerald-800',
      research: 'bg-orange-100 text-orange-800',
      automation: 'bg-red-100 text-red-800',
      ai: 'bg-gray-100 text-gray-800',
      communication: 'bg-cyan-100 text-cyan-800',
      ecommerce: 'bg-violet-100 text-violet-800'
    };

    return typeColors[integrationType] || 'bg-gray-100 text-gray-800';
  }

  /**
   * Get integration status color
   */
  getStatusColor(status: ConnectedIntegration['status']): string {
    const statusColors: Record<ConnectedIntegration['status'], string> = {
      valid: 'text-green-600',
      expired: 'text-yellow-600',
      invalid: 'text-red-600',
      revoked: 'text-red-600'
    };

    return statusColors[status] || 'text-gray-600';
  }

  /**
   * Format integration scopes for display
   */
  formatScopes(scopes: string[]): string[] {
    const scopeDescriptions: Record<string, string> = {
      'campaigns:read': 'Read campaigns',
      'campaigns:write': 'Write campaigns',
      'lists:read': 'Read lists',
      'lists:write': 'Write lists',
      'broadcasts:read': 'Read broadcasts',
      'broadcasts:write': 'Write broadcasts',
      'subscribers:read': 'Read subscribers',
      'subscribers:write': 'Write subscribers',
      'profiles:read': 'Read profiles',
      'profiles:write': 'Write profiles',
      'events:read': 'Read events',
      'events:write': 'Write events',
      'insights:read': 'Read insights',
      'crm.objects.contacts.read': 'Read contacts',
      'crm.objects.contacts.write': 'Write contacts',
      'crm.objects.companies.read': 'Read companies',
      'crm.objects.companies.write': 'Write companies',
      'deals:read': 'Read deals',
      'deals:write': 'Write deals',
      'persons:read': 'Read persons',
      'persons:write': 'Write persons',
      'posts:read': 'Read posts',
      'posts:write': 'Write posts',
      'pages:read': 'Read pages',
      'pages:write': 'Write pages',
      'content:read': 'Read content',
      'content:write': 'Write content',
      'assets:read': 'Read assets',
      'assets:write': 'Write assets',
      'read': 'Read access',
      'write': 'Write access',
      'insert': 'Insert access',
      'file_read': 'Read files',
      'file_write': 'Write files',
      'team_read': 'Read team',
      'design:read': 'Read designs',
      'design:write': 'Write designs',
      'template:read': 'Read templates',
      'chat:write': 'Send messages',
      'channels:read': 'Read channels',
      'users:read': 'Read users',
      'files:write': 'Write files',
      'columns': 'Manage columns',
      'cards': 'Manage cards',
      'boards': 'Manage boards',
      'members': 'Manage members',
      'projects': 'Manage projects',
      'tasks': 'Manage tasks',
      'teams': 'Manage teams',
      'payments': 'Process payments',
      'customers': 'Manage customers',
      'subscriptions': 'Manage subscriptions',
      'invoices': 'Manage invoices',
      'completions:read': 'Read completions',
      'completions:write': 'Write completions',
      'embeddings:read': 'Read embeddings',
      'text:generate': 'Generate text',
      'conversation:create': 'Create conversations',
      'analysis:perform': 'Perform analysis',
      'zaps:read': 'Read zaps',
      'zaps:write': 'Write zaps',
      'triggers:read': 'Read triggers',
      'actions:write': 'Write actions',
      'applets:read': 'Read applets',
      'applets:write': 'Write applets',
      'queries': 'Run queries'
    };

    return scopes.map(scope => scopeDescriptions[scope] || scope);
  }
}

export const integrationService = IntegrationService.getInstance();
