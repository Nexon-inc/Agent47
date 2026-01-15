import { apiClient } from '../api-client';

export interface PlatformConfig {
  name: string;
  display_name: string;
  platform_type: string;
  description: string;
  scopes: string[];
  supported_features: {
    posting: boolean;
    analytics: boolean;
    engagement: boolean;
    scheduling: boolean;
    automation: boolean;
  };
  supports_workspaces: boolean;
  max_users_per_app: number;
}

export interface ConnectedPlatform {
  id: number;
  user_id: number;
  platform_name: string;
  workspace_id?: string;
  workspace_name?: string;
  scopes: string[];
  status: 'active' | 'expired' | 'revoked' | 'invalid';
  is_active: boolean;
  expires_at?: string;
  last_used?: string;
  last_refreshed?: string;
  created_at: string;
  updated_at: string;
  display_name?: string;
  platform_type?: string;
  supported_features?: {
    posting: boolean;
    analytics: boolean;
    engagement: boolean;
    scheduling: boolean;
    automation: boolean;
  };
}

export interface OAuthInitiationResult {
  success: boolean;
  auth_url?: string;
  platform?: string;
  scopes?: string[];
  state?: string;
  error?: string;
}

export interface OAuthCallbackResult {
  success: boolean;
  platform?: string;
  workspace?: string;
  error?: string;
  error_code?: string;
  error_message?: string;
}

export class PlatformOAuthService {
  private static instance: PlatformOAuthService;
  private baseUrl: string;

  private constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  }

  public static getInstance(): PlatformOAuthService {
    if (!PlatformOAuthService.instance) {
      PlatformOAuthService.instance = new PlatformOAuthService();
    }
    return PlatformOAuthService.instance;
  }

  /**
   * Get all available platforms for connection
   */
  async getAvailablePlatforms(): Promise<PlatformConfig[]> {
    try {
      // Use the correct endpoint path
      const response = await apiClient.get('/api/v1/platforms/');
      
      // Handle wrapped response
      const platforms = response?.data || response || [];
      
      if (Array.isArray(platforms)) {
        return platforms;
      } else {
        throw new Error('Invalid response format from backend');
      }
    } catch (error) {
      console.error('Error getting available platforms:', error);
      throw error;
    }
  }

  /**
   * Initiate OAuth connection to a platform
   */
  async initiateConnection(platformName: string): Promise<OAuthInitiationResult> {
    try {
      const response = await apiClient.get(`/api/v1/platforms/connect/${platformName}`);
      
      // Handle wrapped response
      const data = response?.data || response;
      
      if (data?.success || data?.auth_url) {
        return {
          success: true,
          auth_url: data.auth_url,
          platform: data.platform || platformName,
          scopes: data.scopes,
          state: data.state
        };
      } else {
        return {
          success: false,
          error: data?.error || 'Failed to initiate connection'
        };
      }
    } catch (error: any) {
      console.error('Error initiating platform connection:', error);
      return {
        success: false,
        error: error.message || 'Failed to initiate connection'
      };
    }
  }

  /**
   * Get user's connected platforms
   */
  async getConnectedPlatforms(): Promise<ConnectedPlatform[]> {
    try {
      const response = await apiClient.get('/api/v1/platforms/connected');
      
      // Handle wrapped response
      const data = response?.data || response;
      const platforms = data?.platforms || data || [];
      
      if (Array.isArray(platforms)) {
        return platforms;
      } else {
        throw new Error('Invalid response format from backend');
      }
    } catch (error) {
      console.error('Error getting connected platforms:', error);
      throw error;
    }
  }

  /**
   * Disconnect from a platform
   */
  async disconnectPlatform(platformName: string): Promise<{ success: boolean; message?: string; error?: string }> {
    try {
      const response = await apiClient.post(`/api/v1/platforms/disconnect/${platformName}`);
      
      // Handle wrapped response
      const data = response?.data || response;
      
      if (data?.success || response?.success) {
        return {
          success: true,
          message: data?.message || 'Platform disconnected successfully'
        };
      } else {
        return {
          success: false,
          error: data?.error || 'Failed to disconnect platform'
        };
      }
    } catch (error: any) {
      console.error('Error disconnecting platform:', error);
      return {
        success: false,
        error: error.message || 'Failed to disconnect platform'
      };
    }
  }

  /**
   * Refresh platform tokens
   */
  async refreshTokens(platformName: string): Promise<{ success: boolean; message?: string; error?: string }> {
    try {
      const response = await apiClient.post(`/platforms/refresh/${platformName}`);
      
      if (response.success) {
        return {
          success: true,
          message: response.message
        };
      } else {
        return {
          success: false,
          error: response.error || 'Failed to refresh tokens'
        };
      }
    } catch (error: any) {
      console.error('Error refreshing tokens:', error);
      return {
        success: false,
        error: error.message || 'Failed to refresh tokens'
      };
    }
  }

  /**
   * Validate platform access
   */
  async validateAccess(platformName: string, scopes?: string[]): Promise<{ success: boolean; has_access?: boolean; error?: string }> {
    try {
      const params = new URLSearchParams();
      if (scopes) {
        scopes.forEach(scope => params.append('scopes', scope));
      }
      
      const response = await apiClient.get(`/platforms/validate/${platformName}?${params.toString()}`);
      
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
      console.error('Error validating platform access:', error);
      return {
        success: false,
        error: error.message || 'Failed to validate access'
      };
    }
  }

  /**
   * Handle OAuth callback from URL parameters
   */
  handleOAuthCallback(): OAuthCallbackResult {
    if (typeof window === 'undefined') {
      return { success: false, error: 'Not in browser environment' };
    }

    const urlParams = new URLSearchParams(window.location.search);
    const error = urlParams.get('error');
    const errorDescription = urlParams.get('error_description');
    const platform = urlParams.get('platform');
    const workspace = urlParams.get('workspace');

    if (error) {
      return {
        success: false,
        error: error,
        error_code: error,
        error_message: errorDescription || 'OAuth error occurred',
        platform: platform || undefined
      };
    }

    return {
      success: true,
      platform: platform || undefined,
      workspace: workspace || undefined
    };
  }

  /**
   * Redirect to platform OAuth URL
   */
  redirectToOAuth(authUrl: string): void {
    if (typeof window !== 'undefined') {
      window.location.href = authUrl;
    }
  }

  /**
   * Get platform icon and styling
   */
  getPlatformInfo(platformName: string): { icon: string; color: string; bgColor: string } {
    const platformInfo: Record<string, { icon: string; color: string; bgColor: string }> = {
      linkedin: {
        icon: 'linkedin',
        color: 'text-blue-600',
        bgColor: 'bg-blue-600'
      },
      twitter: {
        icon: 'twitter',
        color: 'text-black',
        bgColor: 'bg-black'
      },
      facebook: {
        icon: 'facebook',
        color: 'text-blue-700',
        bgColor: 'bg-blue-700'
      },
      instagram: {
        icon: 'instagram',
        color: 'text-pink-600',
        bgColor: 'bg-gradient-to-r from-purple-500 to-pink-500'
      },
      youtube: {
        icon: 'youtube',
        color: 'text-red-600',
        bgColor: 'bg-red-600'
      },
      tiktok: {
        icon: 'video',
        color: 'text-black',
        bgColor: 'bg-black'
      },
      pinterest: {
        icon: 'image',
        color: 'text-red-500',
        bgColor: 'bg-red-500'
      },
      slack: {
        icon: 'slack',
        color: 'text-purple-600',
        bgColor: 'bg-purple-600'
      },
      hubspot: {
        icon: 'bar-chart',
        color: 'text-orange-500',
        bgColor: 'bg-orange-500'
      },
      salesforce: {
        icon: 'cloud',
        color: 'text-blue-500',
        bgColor: 'bg-blue-500'
      },
      mailchimp: {
        icon: 'mail',
        color: 'text-yellow-500',
        bgColor: 'bg-yellow-500'
      },
      shopify: {
        icon: 'shopping-bag',
        color: 'text-green-600',
        bgColor: 'bg-green-600'
      }
    };

    return platformInfo[platformName] || {
      icon: 'globe',
      color: 'text-gray-600',
      bgColor: 'bg-gray-600'
    };
  }

  /**
   * Check if platform supports a specific feature
   */
  supportsFeature(platform: ConnectedPlatform, feature: keyof ConnectedPlatform['supported_features']): boolean {
    return platform.supported_features?.[feature] || false;
  }

  /**
   * Get platform status color
   */
  getStatusColor(status: ConnectedPlatform['status']): string {
    const statusColors: Record<ConnectedPlatform['status'], string> = {
      active: 'text-green-600',
      expired: 'text-yellow-600',
      revoked: 'text-red-600',
      invalid: 'text-red-600'
    };

    return statusColors[status] || 'text-gray-600';
  }

  /**
   * Format platform scopes for display
   */
  formatScopes(scopes: string[]): string[] {
    const scopeDescriptions: Record<string, string> = {
      'r_liteprofile': 'Read basic profile',
      'r_emailaddress': 'Read email address',
      'w_member_social': 'Write social media posts',
      'rw_organization_admin': 'Manage organization',
      'tweet.read': 'Read tweets',
      'tweet.write': 'Write tweets',
      'users.read': 'Read user information',
      'follows.read': 'Read follows',
      'follows.write': 'Manage follows',
      'pages_manage_posts': 'Manage page posts',
      'pages_read_engagement': 'Read page engagement',
      'pages_show_list': 'View page list',
      'instagram_basic': 'Basic Instagram access',
      'instagram_content_publish': 'Publish Instagram content',
      'user_profile': 'Read user profile',
      'user_media': 'Read user media',
      'https://www.googleapis.com/auth/youtube': 'YouTube access',
      'https://www.googleapis.com/auth/youtube.upload': 'Upload YouTube videos',
      'user.info.basic': 'Read basic user info',
      'video.publish': 'Publish videos',
      'pins:read': 'Read pins',
      'pins:write': 'Write pins',
      'boards:read': 'Read boards',
      'boards:write': 'Write boards',
      'chat:write': 'Send messages',
      'channels:read': 'Read channels',
      'users:read': 'Read users',
      'files:write': 'Write files',
      'crm.objects.contacts.read': 'Read contacts',
      'crm.objects.contacts.write': 'Write contacts',
      'crm.objects.companies.read': 'Read companies',
      'crm.objects.companies.write': 'Write companies',
      'api': 'API access',
      'refresh_token': 'Refresh tokens',
      'id': 'Read user ID',
      'profile': 'Read profile',
      'email': 'Read email',
      'campaigns:read': 'Read campaigns',
      'campaigns:write': 'Write campaigns',
      'lists:read': 'Read lists',
      'lists:write': 'Write lists',
      'read_products': 'Read products',
      'write_products': 'Write products',
      'read_orders': 'Read orders',
      'write_orders': 'Write orders'
    };

    return scopes.map(scope => scopeDescriptions[scope] || scope);
  }
}

export const platformOAuthService = PlatformOAuthService.getInstance();
