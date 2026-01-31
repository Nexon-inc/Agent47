// API Client for Agent47 Frontend
// Handles all communication with the Supabase backend API

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL || 'http://localhost:54321';
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0';

// Supabase client (will be initialized when needed)
let supabaseClient: any = null;

// Initialize Supabase client
const initSupabaseClient = async () => {
  if (!supabaseClient && typeof window !== 'undefined') {
    try {
      // Dynamic import to avoid SSR issues
      const { createClient } = await import('@supabase/supabase-js');
      supabaseClient = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
        auth: {
          autoRefreshToken: true,
          persistSession: true,
          detectSessionInUrl: true
        }
      });
    } catch (error) {
      console.warn('Supabase client not available, falling back to API-only mode:', error);
    }
  }
  return supabaseClient;
};

// Types
export interface User {
  id: number;
  email: string;
  username: string;
  full_name?: string;
  tier: string;
  is_active: boolean;
  is_verified: boolean;
  is_admin?: boolean;
  created_at: string;
  last_login?: string;
  preferences?: Record<string, any>;
  onboarding_completed?: boolean;
  onboarding_completed_at?: string;
  onboarding_data?: OnboardingData;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface SignupData {
  email: string;
  username: string;
  password: string;
  first_name: string;
  last_name: string;
  nickname?: string;
  country?: string;
  continent?: string;
  age?: string;
  purpose?: string;
  business_name?: string;
}

export interface LoginData {
  email: string;
  password: string;
}

export interface PasswordResetData {
  email: string;
}

export interface PasswordChangeData {
  current_password: string;
  new_password: string;
}

export interface OnboardingData {
  // Only profile is persisted server-side; social/tutorials/workflow removed
  profile: {
    role: string;
    industry: string;
    goals: string[];
    otherGoal?: string;
  };
}

export interface OnboardingResponse {
  success: boolean;
  message: string;
  onboarding_data?: OnboardingData;
}

export interface AdminStats {
  total_users: number;
  active_users: number;
  new_users_30_days: number;
  tier_distribution: Record<string, number>;
  verification_rate: number;
  onboarding_completed_users: number;
  onboarding_completion_rate: number;
}

export interface AdminUsers {
  users: User[];
  total: number;
  active_users: number;
}

export interface Agent {
  id: string;
  name: string;
  type: string;
  status: 'online' | 'offline' | 'busy' | 'error' | 'maintenance';
  capabilities: string[];
  metrics: {
    total_tasks: number;
    completed_tasks: number;
    failed_tasks: number;
    success_rate: number;
    active_tasks: number;
    avg_response_time: number;
    memory_usage: number;
    cpu_usage: number;
  };
  last_activity: string;
  version: string;
  description: string;
  is_active: boolean;
}

export interface AgentService {
  id: string;
  agent_id: string;
  service_name: string;
  service_type: string;
  endpoint: string;
  protocol: string;
  status: string;
  response_time_ms: number;
  last_health_check: string;
  error_count: number;
}

export interface AgentCoordination {
  id: string;
  coordinator_agent_id: string;
  coordinated_agent_id: string;
  coordination_type: string;
  status: string;
  priority: number;
  timestamp: string;
  result?: any;
}

export interface IntegrationMetrics {
  total_services: number;
  online_services: number;
  total_communications: number;
  successful_communications: number;
  avg_response_time: number;
  error_rate: number;
}

export interface UserMetrics {
  inactive_users: number;
  verified_users: number;
  onboarding_completed_users: number;
}

// Goals Types
export interface GoalMetric {
  name: string;
  target_value: number;
  current_value: number;
  unit: string;
  weight: number;
  is_primary: boolean;
  progress_percentage: number;
  is_completed: boolean;
}

export interface Goal {
  id: string;
  name: string;
  description: string;
  goal_type: string;
  status: string;
  priority: string;
  start_date: string;
  end_date: string;
  metrics: GoalMetric[];
  assigned_agents: string[];
  created_by: string;
  created_at: string;
  updated_at: string;
  tags: string[];
  budget: number;
  actual_cost: number;
  overall_progress: number;
  is_completed: boolean;
  is_overdue: boolean;
  days_remaining: number;
  days_elapsed: number;
  completion_rate: number;
}

export interface GoalProgress {
  id: number;
  goal_id: string;
  metric_name: string;
  current_value: number;
  timestamp: string;
  updated_by: string;
  notes?: string;
}

export interface GoalActivity {
  id: number;
  goal_id: string;
  activity_type: string;
  description: string;
  performed_by: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface GoalTemplate {
  id: string;
  name: string;
  description: string;
  goal_type: string;
  priority: string;
  metrics: Omit<GoalMetric, 'current_value' | 'progress_percentage' | 'is_completed'>[];
  assigned_agents: string[];
  tags: string[];
}

export interface CreateGoalData {
  name: string;
  description: string;
  goal_type: string;
  priority: string;
  start_date: string;
  end_date: string;
  metrics: Omit<GoalMetric, 'current_value' | 'progress_percentage' | 'is_completed'>[];
  assigned_agents: string[];
  tags: string[];
  budget?: number;
}

export interface UpdateGoalData {
  name?: string;
  description?: string;
  status?: string;
  priority?: string;
  end_date?: string;
  metrics?: GoalMetric[];
  assigned_agents?: string[];
  tags?: string[];
  budget?: number;
}

export interface UpdateGoalProgressData {
  metric_name: string;
  current_value: number;
  notes?: string;
}

export interface GoalsResponse {
  goals: Goal[];
  total: number;
  active_goals: number;
  completed_goals: number;
  overdue_goals: number;
}

export interface GoalAnalytics {
  total_goals: number;
  active_goals: number;
  completed_goals: number;
  overdue_goals: number;
  average_completion_rate: number;
  goals_by_type: Record<string, number>;
  goals_by_priority: Record<string, number>;
  goals_by_status: Record<string, number>;
  recent_activities: GoalActivity[];
  top_performing_agents: Array<{
    agent_name: string;
    goals_completed: number;
    average_progress: number;
  }>;
}

// Billing Types
export interface BillingPlan {
  id: number;
  tier: string;
  name: string;
  description: string;
  price_usd: number;
  billing_cycle: string;
  max_agents: number | null;
  image_generation_limit: number | null;
  features: Record<string, any>;
  is_active: boolean;
}

export interface Subscription {
  id: number;
  tier: string;
  status: string;
  start_date: string;
  end_date: string;
  auto_renew: boolean;
  plan_name: string;
  price_usd: number;
  features: Record<string, any>;
}

export interface Payment {
  id: number;
  amount_usd: number;
  currency: string;
  status: string;
  payment_method: string;
  created_at: string;
  paystack_reference?: string;
}

export interface PaymentResponse {
  success?: boolean;
  message?: string;
  subscription_id?: number;
  status?: string;
  tier?: string;
  start_date?: string;
  end_date?: string;
  authorization_url?: string;
  payment_url?: string; // Keep for backward compatibility if any
  reference?: string;
}

export interface UsageData {
  api_calls_count: number;
  agent_usage: Record<string, any>;
  storage_used_mb: number;
  month: string;
}

export interface RevenueData {
  total_revenue: number;
  monthly_recurring_revenue: number;
  total_subscriptions: number;
  active_subscriptions: number;
  average_revenue_per_user: number;
  churn_rate: number;
}

export interface SubscriptionData {
  id: number;
  user_id: number;
  user_email: string;
  user_name: string;
  tier: string;
  status: string;
  start_date: string;
  end_date: string;
  price_usd: number;
  created_at: string;
}

export interface PaymentData {
  id: number;
  user_id: number;
  user_email: string;
  user_name: string;
  amount_usd: number;
  currency: string;
  status: string;
  payment_method: string;
  created_at: string;
  paystack_reference?: string;
}

// API Client Class
class ApiClient {
  private baseURL: string;
  private accessToken: string | null = null;

  getToken(): string | null {
    return this.accessToken || localStorage.getItem('access_token');
  }
  private refreshToken: string | null = null;

  constructor(baseURL: string = API_BASE_URL) {
    // Normalize baseURL: remove trailing /api/v1 if present to avoid duplication
    // Endpoints already include /api/v1 prefix
    this.baseURL = baseURL.replace(/\/api\/v1\/?$/, '').replace(/\/$/, '');
    this.loadTokensFromStorage();
    // Initialize Supabase client on construction
    this.initializeSupabase();
  }

  private async initializeSupabase(): Promise<void> {
    if (typeof window !== 'undefined') {
      await initSupabaseClient();
    }
  }

  // Token Management
  private loadTokensFromStorage(): void {
    if (typeof window !== 'undefined') {
      this.accessToken = localStorage.getItem('access_token');
      this.refreshToken = localStorage.getItem('refresh_token');
    }
  }

  private saveTokensToStorage(tokens: AuthTokens): void {
    if (typeof window !== 'undefined') {
      // Only persist tokens and user if we actually have a non-empty access token.
      // Some signup flows (e.g. email confirmation required) return no session; in that
      // case we must not treat the user as authenticated or store their profile/tokens.
      if (tokens.access_token) {
        // Store in localStorage for API calls
        localStorage.setItem('access_token', tokens.access_token);
        localStorage.setItem('refresh_token', tokens.refresh_token);
        localStorage.setItem('user', JSON.stringify(tokens.user));

        // ALSO store in cookies for middleware
        const expiresIn = new Date(Date.now() + tokens.expires_in * 1000);
        // Use SameSite=None and Secure to allow cross-site requests from the frontend host
        const cookieAttrs = `path=/; expires=${expiresIn.toUTCString()}; SameSite=None; Secure`;
        document.cookie = `access_token=${tokens.access_token}; ${cookieAttrs}`;
        document.cookie = `refresh_token=${tokens.refresh_token}; ${cookieAttrs}`;
        document.cookie = `user_tier=${tokens.user.tier || 'null'}; ${cookieAttrs}`;
        document.cookie = `onboarding_completed=${tokens.user.onboarding_completed || 'false'}; ${cookieAttrs}`;
      } else {
        // Ensure we don't leave stale auth artifacts in storage
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        // Clear cookies with SameSite=None; Secure to match how they were set
        const expiredAttrs = 'path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=None; Secure';
        document.cookie = `access_token=; ${expiredAttrs}`;
        document.cookie = `refresh_token=; ${expiredAttrs}`;
        document.cookie = `user_tier=; ${expiredAttrs}`;
        document.cookie = `onboarding_completed=; ${expiredAttrs}`;
      }
    }

    this.accessToken = tokens.access_token || null;
    this.refreshToken = tokens.refresh_token || null;
  }

  private clearTokensFromStorage(): void {
    if (typeof window !== 'undefined') {
      // Clear localStorage
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');

      // Clear cookies
      document.cookie = 'access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
      document.cookie = 'refresh_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
      document.cookie = 'user_tier=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
      document.cookie = 'onboarding_completed=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
    }

    this.accessToken = null;
    this.refreshToken = null;
  }

  // HTTP Request Helper
  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit & { suppressTierRedirect?: boolean } = {}
  ): Promise<T> {
    // Ensure tokens are loaded from storage before making request
    this.loadTokensFromStorage();
    // If we don't have an access token locally, try a server-side refresh
    // This helps when authentication is cookie-based (server-set cookies on a different domain).
    if (!this.getToken()) {
      try {
        const refreshed = await this.refreshAccessToken();
        if (refreshed) {
          this.loadTokensFromStorage();
        }
      } catch (err) {
        // ignore - we'll handle 401s below
      }
    }

    const url = `${this.baseURL}${endpoint}`;

    // Add authorization header if token exists
    const token = this.getToken();
    const isFormData = options.body instanceof FormData;
    const headers: Record<string, string> = {
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...(options.headers as Record<string, string> || {}),
    };

    if (token) {
      headers.Authorization = `Bearer ${token}`;
      headers['x-access-token'] = token; // Add custom header for middleware
      // eslint-disable-next-line no-console
      console.debug(`[apiClient] Authorization header set for ${endpoint}`);
    } else {
      console.warn(`[apiClient] No token available for request to ${endpoint}. User may not be authenticated.`);
    }

    const config: RequestInit = {
      ...options,
      headers,
      // Ensure cookies (auth/admin cookies) are sent for cross-origin requests
      credentials: 'include',
    };

    // DEBUG: log token/header state to help debug 401 issues (remove in production)
    try {
      try {
        // Avoid logging full token in production, but allow during debugging
        // eslint-disable-next-line no-console
        console.debug('[apiClient] makeRequest - token present?', !!this.getToken(), 'tokenPreview:', (this.getToken() || '').substring(0, 8));
        // eslint-disable-next-line no-console
        console.debug('[apiClient] makeRequest - headers:', headers);
      } catch (e) { }
      const response = await fetch(url, config);

      // Handle 401 Unauthorized - try to refresh token
      if (response.status === 401 && this.refreshToken) {
        const refreshed = await this.refreshAccessToken();
        if (refreshed) {
          // Retry the original request with new token
          const newToken = this.getToken();
          if (newToken) {
            headers.Authorization = `Bearer ${newToken}`;
            headers['x-access-token'] = newToken;
          }
          const retryResponse = await fetch(url, { ...config, headers, credentials: 'include' });
          return this.handleResponse<T>(retryResponse, endpoint, options.suppressTierRedirect === true);
        } else {
          // Token refresh failed, throw error with details
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || "Authentication failed. Please log in again.");
        }
      }

      return this.handleResponse<T>(response, endpoint, options.suppressTierRedirect === true);
    } catch (error) {
      console.error('API request failed:', error);
      throw new Error('Network error occurred');
    }
  }

  private async handleResponse<T>(response: Response, endpoint: string, suppressTierRedirect: boolean = false): Promise<T> {
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));

      // Handle 401 Unauthorized - improved debugging
      if (response.status === 401) {
        console.error(`[apiClient] 401 Unauthorized for ${endpoint}. CORS or token issue?`, {
          endpoint,
          tokenPresent: !!this.getToken(),
          corsAllowed: response.headers.get('access-control-allow-origin'),
          errorDetail: errorData.detail
        });
      }

      // Handle CORS issues (manifests as 0 status in some cases)
      if (response.status === 0) {
        console.error(`[apiClient] CORS Error detected for ${endpoint}. Check that your Vercel URL is in BACKEND_CORS_ORIGINS.`);
        throw new Error("CORS error: Backend not allowing requests from this frontend. Contact admin.");
      }

      // Handle tier validation errors - only redirect if user hasn't selected a tier yet
      if (response.status === 403 && errorData.detail && errorData.detail.includes("Tier selection required")) {
        // Check if user has a tier selected (they should have one after signup)
        const authStore = require('@/lib/stores/auth-store').useAuthStore.getState();
        const user = authStore?.user;

        // If user has a tier (even if free), don't redirect - they've already made a choice
        if (user?.tier) {
          // User has a tier, so this is a different 403 error - just throw it
          throw new Error(errorData.detail || "Access denied");
        }

        // If caller asked to suppress automatic redirect (e.g., background calls), just throw
        if (suppressTierRedirect) {
          throw new Error("Tier selection required. Background call suppressed redirect.");
        }

        // If we're already on the pricing page, don't force a redirect (avoids reload loops)
        if (typeof window !== 'undefined') {
          const currentPath = window.location.pathname || '';
          if (currentPath.startsWith('/pricing')) {
            throw new Error("Tier selection required. Already on pricing page.");
          }

          // Redirect to pricing page and include return path
          window.location.href = '/pricing?redirect=' + encodeURIComponent(window.location.pathname);
        }

        throw new Error("Tier selection required. Redirecting to pricing page.");
      }

      // Handle 409 Conflict errors with specific field information
      if (response.status === 409) {
        const detail = errorData.detail || errorData.message || '';

        // Check for specific field conflicts
        if (detail.toLowerCase().includes('email') || detail.toLowerCase().includes('e-mail')) {
          throw new Error("This email address is already registered. Please use a different email or try logging in.");
        } else if (detail.toLowerCase().includes('username')) {
          throw new Error("This username is already taken. Please choose a different username.");
        } else if (detail.toLowerCase().includes('phone') || detail.toLowerCase().includes('mobile')) {
          throw new Error("This phone number is already registered. Please use a different phone number.");
        } else if (detail.toLowerCase().includes('duplicate') || detail.toLowerCase().includes('unique')) {
          throw new Error("This information is already registered. Please check your email, username, or phone number and try again.");
        } else {
          throw new Error(`Registration failed: ${detail || 'A user with this information already exists.'}`);
        }
      }

      // Handle 400 Bad Request errors
      if (response.status === 400) {
        const detail = errorData.detail || errorData.message || '';

        if (detail.toLowerCase().includes('password')) {
          throw new Error("Password requirements not met. Please ensure your password is at least 8 characters long.");
        } else if (detail.toLowerCase().includes('email')) {
          throw new Error("Please enter a valid email address.");
        } else if (detail.toLowerCase().includes('username')) {
          throw new Error("Username must be at least 3 characters long and contain only letters, numbers, and underscores.");
        } else {
          throw new Error(`Invalid input: ${detail || 'Please check your information and try again.'}`);
        }
      }

      // Handle 404 errors more gracefully
      if (response.status === 404) {
        console.warn(`Endpoint not found: ${response.url}`);
        throw new Error(errorData.detail || errorData.message || 'Endpoint not found');
      }

      throw new Error(errorData.detail || errorData.message || `HTTP ${response.status}: ${response.statusText}`);
    }

    const jsonData = await response.json();
    // Log response for debugging
    if (endpoint.includes('/auth/me') || endpoint.includes('/account')) {
      console.log(`Response from ${endpoint}:`, jsonData);
    }
    return jsonData;
  }

  // Authentication Methods
  async signup(data: SignupData): Promise<AuthTokens> {
    // Use backend API for signup (skip Supabase direct calls)
    const response = await this.makeRequest<AuthTokens>('/api/v1/auth/signup', {
      method: 'POST',
      body: JSON.stringify(data),
    });

    this.saveTokensToStorage(response);
    return response;
  }

  async login(data: LoginData): Promise<AuthTokens> {
    // Use backend API for login (skip Supabase direct calls)
    const response = await this.makeRequest<AuthTokens>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    });

    this.saveTokensToStorage(response);
    return response;
  }

  async logout(): Promise<void> {
    try {
      // Use backend API for logout
      await this.makeRequest('/api/v1/auth/logout', {
        method: 'POST',
      });
    } catch (error) {
      // Continue with logout even if API call fails
      console.warn('Logout API call failed:', error);
    } finally {
      this.clearTokensFromStorage();
    }
  }

  async refreshAccessToken(): Promise<boolean> {
    const supabase = await initSupabaseClient();

    if (supabase) {
      try {
        // Supabase handles token refresh automatically
        const { data: { session }, error } = await supabase.auth.getSession();

        if (error) {
          console.error('Session refresh failed:', error);
          this.clearTokensFromStorage();
          return false;
        }

        if (session) {
          this.accessToken = session.access_token;
          this.refreshToken = session.refresh_token;

          if (typeof window !== 'undefined') {
            localStorage.setItem('access_token', session.access_token);
            localStorage.setItem('refresh_token', session.refresh_token);
          }
          return true;
        }
      } catch (error) {
        console.error('Token refresh failed:', error);
      }
    } else {
      // Fallback to API-only mode
      if (!this.refreshToken) {
        return false;
      }

      try {
        const refreshBody = this.refreshToken ? JSON.stringify({ refresh_token: this.refreshToken }) : undefined;
        const response = await fetch(`${this.baseURL}/api/v1/auth/refresh`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: refreshBody,
          credentials: 'include',
        });

        if (response.ok) {
          const tokens = await response.json();
          this.accessToken = tokens.access_token;
          if (typeof window !== 'undefined') {
            localStorage.setItem('access_token', tokens.access_token);
          }
          return true;
        }
      } catch (error) {
        console.error('Token refresh failed:', error);
      }
    }

    // If refresh failed, clear all tokens
    this.clearTokensFromStorage();
    return false;
  }

  async getCurrentSession(): Promise<any> {
    const supabase = await initSupabaseClient();

    if (supabase) {
      const { data: { session }, error } = await supabase.auth.getSession();
      if (error) {
        console.error('Failed to get session:', error);
        return null;
      }
      return session;
    }

    return null;
  }

  async resetPasswordRequest(data: PasswordResetData): Promise<{ message: string }> {
    const supabase = await initSupabaseClient();

    if (supabase) {
      const { error } = await supabase.auth.resetPasswordForEmail(data.email, {
        redirectTo: `${window.location.origin}/auth/reset-password`
      });

      if (error) {
        throw new Error(error.message);
      }

      return { message: 'Password reset email sent successfully' };
    }

    // Fallback to API-only mode
    return this.makeRequest<{ message: string }>('/api/v1/auth/reset-password-request', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async changePassword(data: PasswordChangeData): Promise<{ message: string }> {
    const supabase = await initSupabaseClient();

    if (supabase) {
      const { error } = await supabase.auth.updateUser({
        password: data.new_password
      });

      if (error) {
        throw new Error(error.message);
      }

      return { message: 'Password updated successfully' };
    }

    // Fallback to API-only mode
    return this.makeRequest<{ message: string }>('/api/v1/auth/change-password', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getCurrentUser(): Promise<User> {
    // Use backend API for getting current user
    return this.makeRequest<User>('/api/v1/auth/me');
  }

  async getAccountData(): Promise<User> {
    // Get comprehensive account data including onboarding and profile info
    try {
      const data = await this.makeRequest<User>('/api/v1/auth/me');
      console.log("getAccountData response:", data);
      return data;
    } catch (error) {
      console.error("getAccountData error:", error);
      throw error;
    }
  }

  // Alias for getOnboardingData - removed duplicate getAccountData naming to fix lint errors
  async getAccountOnboardingData(): Promise<OnboardingResponse> {
    return this.getOnboardingData();
  }

  // Onboarding Methods
  async saveOnboardingData(data: OnboardingData): Promise<OnboardingResponse> {
    return this.makeRequest<OnboardingResponse>('/api/v1/onboarding/save', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getOnboardingData(): Promise<OnboardingResponse> {
    return this.makeRequest<OnboardingResponse>('/api/v1/onboarding/data');
  }

  async updateOnboardingData(data: OnboardingData): Promise<OnboardingResponse> {
    return this.makeRequest<OnboardingResponse>('/api/v1/onboarding/update', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  // Save selected agents
  async saveSelectedAgents(agentIds: string[]): Promise<any> {
    return this.makeRequest('/api/v1/account/selected-agents', {
      method: 'POST',
      body: JSON.stringify({ agents: agentIds }),
    });
  }

  // Billing Methods
  async getSubscription(opts?: { suppressRedirect?: boolean }): Promise<Subscription> {
    return this.makeRequest<Subscription>('/api/v1/billing/subscription', {
      suppressTierRedirect: !!opts?.suppressRedirect,
    } as any);
  }

  // Backwards-compatible getBillingPlans with optional suppression
  async getBillingPlans(opts?: { suppressRedirect?: boolean }): Promise<BillingPlan[]> {
    return this.makeRequest<BillingPlan[]>('/api/v1/billing/plans', {
      suppressTierRedirect: !!opts?.suppressRedirect,
    } as any);
  }

  async createSubscription(
    tier: string,
    paymentMethod: string = 'paystack',
    billingPeriod: string = 'monthly',
    opts?: { suppressRedirect?: boolean }
  ): Promise<PaymentResponse> {
    return this.makeRequest<PaymentResponse>('/api/v1/billing/subscribe', {
      method: 'POST',
      body: JSON.stringify({
        tier,
        payment_method: paymentMethod,
        billing_period: billingPeriod
      }),
      // forward suppress flag so makeRequest/handleResponse won't auto-redirect
      suppressTierRedirect: !!opts?.suppressRedirect,
    } as any);
  }

  async verifyPayment(reference: string): Promise<PaymentResponse> {
    return this.makeRequest<PaymentResponse>(`/api/v1/billing/verify?reference=${reference}`);
  }

  async cancelSubscription(reason: string = 'User requested cancellation'): Promise<{ message: string }> {
    return this.makeRequest<{ message: string }>('/api/v1/billing/cancel', {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  }

  async getPaymentHistory(limit: number = 10): Promise<Payment[]> {
    return this.makeRequest<Payment[]>(`/billing/payment-history?limit=${limit}`);
  }

  async getUserUsage(): Promise<UsageData> {
    return this.makeRequest<UsageData>('/api/v1/billing/usage');
  }

  // Admin Methods
  async getAdminStats(): Promise<AdminStats> {
    return this.makeRequest<AdminStats>('/admin/stats');
  }

  async getAllUsers(): Promise<AdminUsers> {
    return this.makeRequest<AdminUsers>('/admin/users');
  }

  async getAdminRevenue(): Promise<RevenueData> {
    return this.makeRequest<RevenueData>('/admin/billing/revenue');
  }

  async getAdminSubscriptions(): Promise<SubscriptionData[]> {
    return this.makeRequest<SubscriptionData[]>('/admin/billing/subscriptions');
  }

  async getAdminPayments(): Promise<PaymentData[]> {
    return this.makeRequest<PaymentData[]>('/admin/billing/payments');
  }

  // Goals Methods
  async getGoals(page: number = 1, limit: number = 10, status?: string): Promise<GoalsResponse> {
    const params = new URLSearchParams({ page: page.toString(), limit: limit.toString() });
    if (status) {
      params.append('status', status);
    }
    return this.makeRequest<GoalsResponse>(`/goals?${params.toString()}`);
  }

  async getGoalById(id: string): Promise<Goal> {
    return this.makeRequest<Goal>(`/goals/${id}`);
  }

  async createGoal(data: CreateGoalData): Promise<Goal> {
    return this.makeRequest<Goal>('/goals', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateGoal(id: string, data: UpdateGoalData): Promise<Goal> {
    return this.makeRequest<Goal>(`/goals/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async updateGoalProgress(goalId: string, data: UpdateGoalProgressData): Promise<Goal> {
    return this.makeRequest<Goal>(`/goals/${goalId}/progress`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async getGoalProgress(goalId: string): Promise<GoalProgress[]> {
    return this.makeRequest<GoalProgress[]>(`/goals/${goalId}/progress`);
  }

  async getGoalActivities(goalId: string): Promise<GoalActivity[]> {
    return this.makeRequest<GoalActivity[]>(`/goals/${goalId}/activities`);
  }

  async getGoalTemplates(): Promise<GoalTemplate[]> {
    return this.makeRequest<GoalTemplate[]>('/goals/templates');
  }

  async getGoalAnalytics(): Promise<GoalAnalytics> {
    return this.makeRequest<GoalAnalytics>('/goals/analytics');
  }

  // Agent Management Methods
  async getAgents(): Promise<Agent[]> {
    return this.makeRequest<Agent[]>('/admin/agents');
  }

  async getAgentById(id: string): Promise<Agent> {
    return this.makeRequest<Agent>(`/admin/agents/${id}`);
  }

  async getAgentServices(agentId: string): Promise<AgentService[]> {
    return this.makeRequest<AgentService[]>(`/admin/agents/${agentId}/services`);
  }

  async getAgentCoordinations(agentId?: string): Promise<AgentCoordination[]> {
    const url = agentId ? `/admin/agents/${agentId}/coordinations` : '/admin/agents/coordinations';
    return this.makeRequest<AgentCoordination[]>(url);
  }

  async getAgentIntegrationStatus(agentId: string): Promise<any> {
    return this.makeRequest<any>(`/admin/agents/${agentId}/integration-status`);
  }

  async getAllAgentsIntegrationStatus(): Promise<any[]> {
    return this.makeRequest<any[]>('/admin/agents/integration-status');
  }

  async restartAgent(agentId: string): Promise<void> {
    return this.makeRequest<void>(`/admin/agents/${agentId}/restart`, {
      method: 'POST',
    });
  }

  async stopAgent(agentId: string): Promise<void> {
    return this.makeRequest<void>(`/admin/agents/${agentId}/stop`, {
      method: 'POST',
    });
  }

  async configureAgent(agentId: string, config: any): Promise<Agent> {
    return this.makeRequest<Agent>(`/admin/agents/${agentId}/configure`, {
      method: 'PUT',
      body: JSON.stringify(config),
    });
  }

  // Integration Management Methods
  async getIntegrationServices(): Promise<AgentService[]> {
    return this.makeRequest<AgentService[]>('/admin/integration/services');
  }

  async getIntegrationMetrics(): Promise<IntegrationMetrics> {
    return this.makeRequest<IntegrationMetrics>('/admin/integration/metrics');
  }

  async getServiceStatus(serviceId: string): Promise<any> {
    return this.makeRequest<any>(`/admin/integration/services/${serviceId}/status`);
  }

  async getAllServicesStatus(): Promise<any[]> {
    return this.makeRequest<any[]>('/admin/integration/services/status');
  }

  async registerAgentService(data: any): Promise<AgentService> {
    return this.makeRequest<AgentService>('/admin/integration/services', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async sendAgentMessage(senderId: string, receiverId: string, messageType: string, content: string, metadata?: any): Promise<boolean> {
    return this.makeRequest<boolean>('/admin/integration/communications', {
      method: 'POST',
      body: JSON.stringify({
        sender_agent_id: senderId,
        receiver_agent_id: receiverId,
        message_type: messageType,
        content,
        metadata
      }),
    });
  }

  // Utility Methods
  isAuthenticated(): boolean {
    return !!this.accessToken;
  }

  getCurrentUserFromStorage(): User | null {
    if (typeof window !== 'undefined') {
      const userStr = localStorage.getItem('user');
      return userStr ? JSON.parse(userStr) : null;
    }
    return null;
  }

  getAccessToken(): string | null {
    return this.accessToken;
  }

  // Admin Billing APIs
  async getAdminBillingSubscriptions(): Promise<{ subscriptions: any[] }> {
    return this.makeRequest('/admin/billing/subscriptions');
  }

  async getAdminBillingActivity(): Promise<{ activities: any[] }> {
    return this.makeRequest('/admin/billing/activity');
  }

  async getAdminBillingAnalytics(): Promise<any> {
    return this.makeRequest('/admin/billing/analytics');
  }

  async getAdminRevenueData(): Promise<any> {
    return this.makeRequest('/admin/billing/revenue');
  }

  // Home Dashboard Methods
  async getUserTasks(): Promise<any[]> {
    return this.makeRequest<any[]>('/intercommunication/tasks');
  }

  async getTaskSummaries(): Promise<any[]> {
    return this.makeRequest<any[]>('/intercommunication/summaries');
  }

  async getSelectedAgents(options?: { suppressTierRedirect?: boolean }): Promise<any[]> {
    const response = await this.makeRequest<any>('/api/v1/account/selected-agents', {
      suppressTierRedirect: options?.suppressTierRedirect || false
    });
    // Ensure we return an array even if backend returns wrapped response
    return Array.isArray(response) ? response : (response?.data || response?.agents || []);
  }

  async getSystemStatus(): Promise<any> {
    return this.makeRequest<any>('/health');
  }



  // Agent Status Management
  async updateAgentStatus(agentId: string, status: "active" | "paused" | "inactive"): Promise<{ data: any }> {
    return this.makeRequest<{ data: any }>('/api/v1/account/selected-agents/status', {
      method: 'PUT',
      body: JSON.stringify({
        agent_id: agentId,
        status: status
      }),
    })
  }

  async updateAgentSettings(agentId: string, settings: Record<string, any>, customInstructions?: string): Promise<{ data: any }> {
    // Legacy method - use updateAgentConfiguration instead
    return this.updateAgentConfiguration(agentId, customInstructions, settings)
  }

  async updateAgentConfiguration(
    agentId: string,
    customInstructions?: string,
    preferences?: Record<string, any>
  ): Promise<{ data: any }> {
    return this.makeRequest<{ data: any }>(`/api/v1/account/selected-agents/configuration`, {
      method: 'PUT',
      body: JSON.stringify({
        agent_id: agentId,
        custom_instructions: customInstructions,
        preferences: preferences
      }),
    })
  }

  async getAgentConfiguration(agentId: string): Promise<{ data: any }> {
    return this.makeRequest<{ data: any }>(`/api/v1/account/selected-agents/${agentId}/configuration`)
  }

  async getAgentHealth(): Promise<{ data: any }> {
    return this.makeRequest('/api/v1/account/agent-health', { method: 'GET' })
  }

  async getSingleAgentHealth(agentId: string): Promise<{ data: any }> {
    return this.makeRequest(`/api/v1/account/agent-health/${agentId}`, { method: 'GET' })
  }

  // Intercommunication Management
  async updateIntercommunicationSetting(enabled: boolean): Promise<{ data: any }> {
    return this.makeRequest('/api/v1/intercommunication/intercommunication', {
      method: 'PUT', // Changed to PUT to match backend router
      body: JSON.stringify({ enabled })
    })
  }

  async getIntercommunicationSetting(): Promise<{ data: any }> {
    return this.makeRequest('/api/v1/intercommunication/intercommunication', { method: 'GET' })
  }

  // Generic GET method for backward compatibility
  async get(endpoint: string): Promise<{ data: any }> {
    // Use endpoint as-is - makeRequest will handle the full URL
    const data = await this.makeRequest<any>(endpoint);
    return { data };
  }

  // Generic POST method
  async post(endpoint: string, data?: any, options: any = {}): Promise<{ data: any }> {
    const isFormData = data instanceof FormData;
    const response = await this.makeRequest(endpoint, {
      method: 'POST',
      body: isFormData ? data : (data ? JSON.stringify(data) : undefined),
      ...options
    });
    return { data: response };
  }

  // Generic PUT method
  async put(endpoint: string, data?: any, options: any = {}): Promise<{ data: any }> {
    const isFormData = data instanceof FormData;
    const response = await this.makeRequest(endpoint, {
      method: 'PUT',
      body: isFormData ? data : (data ? JSON.stringify(data) : undefined),
      ...options
    });
    return { data: response };
  }

  // Analytics Methods
  async getAnalyticsSummary(periodDays: number, agentId?: string): Promise<any> {
    const params = new URLSearchParams({
      period_days: periodDays.toString(),
      ...(agentId && agentId !== 'all' && { agent_id: agentId })
    });
    return this.makeRequest<any>(`/analytics/summary?${params.toString()}`);
  }

  async getAnalyticsChartData(metricType: string, periodDays: number, agentId?: string, groupBy: string = 'day'): Promise<any> {
    const params = new URLSearchParams({
      metric_type: metricType,
      period_days: periodDays.toString(),
      group_by: groupBy,
      ...(agentId && agentId !== 'all' && { agent_id: agentId })
    });
    return this.makeRequest<any>(`/analytics/chart-data?${params.toString()}`);
  }

  async getAnalyticsUsageDistribution(periodDays: number): Promise<any> {
    return this.makeRequest<any>(`/analytics/usage-distribution?period_days=${periodDays}`);
  }

  async getAnalyticsDetailedData(periodDays: number, agentId?: string, limit: number = 50): Promise<any> {
    const params = new URLSearchParams({
      period_days: periodDays.toString(),
      limit: limit.toString(),
      ...(agentId && agentId !== 'all' && { agent_id: agentId })
    });
    return this.makeRequest<any>(`/analytics/detailed-data?${params.toString()}`);
  }

  async exportAnalytics(periodDays: number, format: string = 'csv'): Promise<any> {
    return this.makeRequest<any>(`/analytics/export?period_days=${periodDays}&format=${format}`);
  }

  // Platform Methods
  async getAvailablePlatforms(): Promise<any[]> {
    return this.makeRequest<any[]>('/platforms/');
  }

  async getConnectedPlatforms(): Promise<any[]> {
    return this.makeRequest<any[]>('/platforms/connected');
  }

  async getPlatformMetrics(): Promise<any> {
    return this.makeRequest<any>('/platforms/metrics');
  }

  // Integration Methods
  async getIntegrations(): Promise<any[]> {
    return this.makeRequest<any[]>('/integrations/');
  }

  async getIntegrationUsage(): Promise<any[]> {
    return this.makeRequest<any[]>('/integrations/usage');
  }

  async getIntegrationStats(): Promise<any> {
    return this.makeRequest<any>('/integrations/stats');
  }

  // Agent-specific Methods
  async getAgentData(agentId: string, endpoint: string): Promise<any> {
    return this.makeRequest<any>(`/agents/${agentId}/${endpoint}`);
  }

  // Team Methods
  async getTeams(): Promise<any[]> {
    return this.makeRequest<any[]>('/teams/');
  }

  async getTeamStats(): Promise<any> {
    return this.makeRequest<any>('/teams/stats');
  }

  async getTeamActivities(limit: number = 20): Promise<any[]> {
    return this.makeRequest<any[]>(`/teams/activities?limit=${limit}`);
  }

  async getTeamMembers(teamId: string): Promise<any[]> {
    return this.makeRequest<any[]>(`/teams/${teamId}/members`);
  }

  // Calendar Methods
  async getCalendarEvents(startDate: string, endDate: string): Promise<any[]> {
    return this.makeRequest<any[]>(`/calendar/events?start_date=${startDate}&end_date=${endDate}`);
  }

  async getCalendarStats(): Promise<any> {
    return this.makeRequest<any>('/calendar/stats');
  }

  // Notification Methods
  async getNotifications(): Promise<any[]> {
    return this.makeRequest<any[]>('/notifications/');
  }

  async getNotificationSummary(): Promise<any> {
    return this.makeRequest<any>('/notifications/summary');
  }
}

// Create singleton instance
export const apiClient = new ApiClient();
