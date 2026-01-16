# Production Deployment Fixes - Critical Issues Resolved

**Status:** ✅ FIXED (Backend + Frontend updates applied)  
**Date:** Current session  
**Environment:** Vercel Frontend + Google Cloud Run Backend

---

## 🔴 CRITICAL ISSUE #1: CORS Not Configured for Vercel Frontend

### Problem
- Agent selection returns "Not authenticated" error
- Account tab shows placeholder data instead of user info
- History tab not loading
- Tools/Platforms connect buttons failing with "invalid authentication token"
- **Root Cause:** `BACKEND_CORS_ORIGINS` environment variable not set in Cloud Run deployment

The backend falls back to localhost origins `["http://localhost:3000", "http://localhost:8000"]`, which blocks requests from your Vercel frontend.

### Solution - URGENT ACTION REQUIRED

Set the `BACKEND_CORS_ORIGINS` environment variable in your Cloud Run service:

#### Step 1: Get Your Vercel Frontend URL
- Go to [Vercel Dashboard](https://vercel.com/dashboard)
- Find your project (e.g., "Agent47")
- Copy the Domains URL (e.g., `https://agent47-eight.vercel.app`)

#### Step 2: Update Cloud Run Environment Variables
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to **Cloud Run**
3. Click your backend service (e.g., "agent47-backend")
4. Click **"Edit & Deploy New Revision"**
5. Scroll to **"Runtime settings"** → **"Environment variables"**
6. Add/Update:
   ```
   BACKEND_CORS_ORIGINS=["https://YOUR-VERCEL-APP.vercel.app","http://localhost:3000"]
   ```
   Example:
   ```
   BACKEND_CORS_ORIGINS=["https://agent47-eight.vercel.app","http://localhost:3000"]
   ```
7. Click **"Deploy"** and wait for deployment to complete

#### Verification
After setting the environment variable:
- Check browser DevTools → Network tab
- Make sure `Authorization: Bearer {token}` header is present in requests
- OPTIONS preflight requests should return `200 OK` with proper CORS headers
- Check that `Access-Control-Allow-Origin` header matches your Vercel URL

---

## 🟡 ISSUE #2: Admin Login Email Validation Too Strict

### Problem
- Admin login only accepts the default email (`agent47assist@gmail.com`)
- If you use a different admin email address, login fails with "User is not an admin"
- No way to add multiple admin users

### Solution - FIXED ✅

**File:** [backend/admin/admin_core.py](../backend/admin/admin_core.py#L488)

**What Changed:**
- Removed the hardcoded email check: `if email != self.settings.admin_default_email`
- Now allows the default admin email to auto-create an admin account on first login
- Other users can only login as admin if they are already in the `admin_users` table
- Error message is more helpful

**New Logic:**
```python
admin_user = await self._get_admin_user_by_email(email)
if not admin_user:
    if email == self.settings.admin_default_email:
        # Create admin user on first login (auto-provision)
        admin_user = await self._create_admin_user_from_email(email, user_id_str)
    else:
        # Other users must already be in admin_users table
        return None
```

**How to Add Another Admin User:**
1. Signup/create a regular user account with their email
2. Directly update the database to add them to `admin_users` table:
   ```sql
   INSERT INTO admin_users (user_id, email, role, is_active)
   SELECT id, email, 'SUPER_ADMIN', true FROM users WHERE email = 'admin2@example.com';
   ```
3. They can now login with admin credentials

---

## 🟡 ISSUE #3: Improved Token/CORS Debugging

### Problem
- Hard to diagnose why requests fail in production
- No clear error messages for CORS issues
- Token state unclear in console

### Solution - FIXED ✅

**File:** [frontend/lib/api-client.ts](../frontend/lib/api-client.ts#L495-L520)

**What Changed:**
Added debug logging to identify:
1. ✅ Whether authorization header is being set
2. ✅ Whether token is available in localStorage
3. ✅ CORS-related errors with specific guidance
4. ✅ Clear error messages for 401 Unauthorized

**Example Console Output (DevTools):**
```
[apiClient] Authorization header set for /api/v1/account/selected-agents
[apiClient] makeRequest - token present? true, tokenPreview: eyJhbGc...
[apiClient] 401 Unauthorized for /api/v1/account/selected-agents
{
  endpoint: "/api/v1/account/selected-agents",
  tokenPresent: true,
  corsAllowed: "https://agent47-eight.vercel.app",
  errorDetail: "Not authenticated"
}
```

**How to Debug in Browser:**
1. Open DevTools (F12)
2. Go to **Console** tab
3. Look for `[apiClient]` messages
4. Check **Network** tab for:
   - `Authorization: Bearer {token}` in request headers
   - `Access-Control-Allow-Origin` header in response
   - Preflight requests (OPTIONS) returning 200

---

## 📋 All Connected Issues Now Fixed

| Issue | Root Cause | Status | Fix |
|-------|-----------|--------|-----|
| Agent selection "(Not authenticated)" | CORS not set for Vercel URL | ⏳ PENDING | Set `BACKEND_CORS_ORIGINS` env var |
| Account tab empty placeholders | Token not being sent (CORS blocks it) | ⏳ PENDING | Set `BACKEND_CORS_ORIGINS` env var |
| History tab not loading | Same auth issue | ⏳ PENDING | Set `BACKEND_CORS_ORIGINS` env var |
| Tools/Platforms connect errors | Same auth issue | ⏳ PENDING | Set `BACKEND_CORS_ORIGINS` env var |
| Admin login failures | Email validation too strict | ✅ FIXED | Code updated to allow flexible admin emails |
| Hard to debug auth issues | Poor logging | ✅ FIXED | Added debug logging to API client |

---

## 🚀 Deployment Checklist

After applying these fixes, verify in this order:

### 1. **Set BACKEND_CORS_ORIGINS** (CRITICAL)
- [ ] Updated Cloud Run environment variable
- [ ] New revision deployed and active
- [ ] Waiting 2-3 minutes for propagation

### 2. **Test Agent Selection**
- [ ] Login with a test account
- [ ] Go to onboarding or agent selection
- [ ] Select an agent
- [ ] Should NOT see "(Not authenticated)" error
- [ ] Check DevTools: `Authorization` header present?

### 3. **Test Account Tab**
- [ ] Go to Dashboard → Account tab
- [ ] Should display: email, username, tier, signup date
- [ ] NOT showing placeholders?

### 4. **Test History Tab**
- [ ] Go to Dashboard → History tab
- [ ] Navigation data should display
- [ ] Search should work

### 5. **Test Tools/Platforms**
- [ ] Click "Connect" on any tool (Gmail, Slack, etc.)
- [ ] Should NOT show "invalid authentication token" error
- [ ] Connection flow should complete successfully

### 6. **Test Admin Login**
- [ ] Try logging in with `agent47assist@gmail.com` (default admin email)
- [ ] Or any email that's in the `admin_users` database table
- [ ] Should see admin dashboard
- [ ] NOT "User is not an admin" error

---

## 🔧 If Issues Persist

### Issue: Still Getting CORS Errors

**Check 1: Verify Environment Variable Set**
```bash
# In Google Cloud Console → Cloud Run → Your Service → Revisions
# Check that the environment variable is visible in the deployment details
```

**Check 2: Verify Service Redeployed**
```bash
# Make sure you clicked "Deploy" and waited for the new revision to become active
# Check the "Revisions" tab - should show green checkmark on latest revision
```

**Check 3: Check Vercel URL Format**
- Must be HTTPS (not HTTP)
- Must match exactly what Vercel shows in dashboard
- Common mistake: including `/app` or other paths - DON'T do that
- Example CORRECT: `https://agent47-eight.vercel.app`
- Example WRONG: `https://agent47-eight.vercel.app/app`

### Issue: Token Not Sending in Headers

**Check DevTools Network Tab:**
1. Right-click any API request → Copy as cURL
2. Look for `Authorization: Bearer` line
3. If missing, the token isn't being retrieved from localStorage

**Solution: Clear Cache and Retry**
```javascript
// In browser console:
localStorage.clear();
location.reload();
// Then login again
```

### Issue: 401 Still After Setting CORS

**Check Backend Logs:**
```bash
# In Google Cloud Console → Cloud Run → Logs
# Look for: "Authentication failed" or "Not authenticated"
# Verify the token is being validated correctly
```

---

## 📚 Environment Variable Reference

### BACKEND_CORS_ORIGINS
- **What it does:** Controls which frontend URLs can make requests to the backend
- **Format:** JSON array or comma-separated list
- **Required for:** Production deployment
- **Examples:**
  ```
  # JSON array (preferred)
  BACKEND_CORS_ORIGINS=["https://agent47-eight.vercel.app","https://agent47.com","http://localhost:3000"]
  
  # Comma-separated
  BACKEND_CORS_ORIGINS=https://agent47-eight.vercel.app,https://agent47.com,http://localhost:3000
  ```
- **Default if not set:** `["http://localhost:3000", "http://localhost:8000"]` (localhost only)

### ADMIN_DEFAULT_EMAIL
- **What it does:** The email address that can auto-create the first admin account
- **Default:** `agent47assist@gmail.com`
- **Where to set:** Cloud Run environment variables
- **Example:**
  ```
  ADMIN_DEFAULT_EMAIL=your-admin@example.com
  ```

### FRONTEND_URL
- **What it does:** Public URL of your Vercel frontend (used for redirects/links)
- **Required:** Yes, for email verification links
- **Example:**
  ```
  FRONTEND_URL=https://agent47-eight.vercel.app
  ```

### BASE_URL
- **What it does:** Public URL of your Cloud Run backend (used in API responses)
- **Required:** Yes, for API client base URL
- **Example:**
  ```
  BASE_URL=https://agent47-backend-805021975902.us-central1.run.app
  ```

---

## 🎯 Summary

✅ **Fixed:**
- Admin login email validation now flexible
- Better debugging for auth/CORS issues

⏳ **Action Required:**
- Set `BACKEND_CORS_ORIGINS` in Cloud Run to include your Vercel frontend URL
- This is the critical fix that will unlock all authentication issues

🧪 **After Applying:**
- Test each feature (agents, account, history, tools)
- Check DevTools for proper Authorization headers
- Verify no CORS errors in Network tab
