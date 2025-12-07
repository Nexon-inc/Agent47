# Paystack Webhook Setup Guide

## ❌ Can Paystack Webhooks Work with localhost:3000?

**Answer: NO** - Paystack webhooks **cannot** work with `localhost:3000` or any local URL.

### Why Localhost Doesn't Work

1. **Paystack servers need to reach your endpoint** - They can't access `localhost` on your computer
2. **Webhooks require public URLs** - Paystack needs to send HTTP POST requests to your server
3. **Security** - Localhost is not accessible from the internet

## ✅ Solutions for Paystack Webhooks

### Option 1: Development - Use ngrok (Recommended for Testing)

**ngrok** creates a public tunnel to your localhost:

```bash
# Install ngrok
# Download from https://ngrok.com/download

# Start your backend on localhost:8000
cd backend
python main.py

# In another terminal, create tunnel
ngrok http 8000

# You'll get a URL like: https://abc123.ngrok.io
# Use this URL for Paystack webhook: https://abc123.ngrok.io/api/v1/billing/webhook/paystack
```

**Steps:**
1. Start your backend locally on port 8000
2. Run `ngrok http 8000`
3. Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)
4. In Paystack dashboard, set webhook URL to: `https://abc123.ngrok.io/api/v1/billing/webhook/paystack`
5. Test payments - webhooks will work!

**Note:** Free ngrok URLs change each time you restart. For production, use a real domain.

### Option 2: Production - Use Your Deployed Domain

When deployed to GCP (or any cloud provider):

1. **Deploy your backend** to GCP (e.g., `https://api.agent47.com`)
2. **Set webhook URL in Paystack:**
   ```
   https://api.agent47.com/api/v1/billing/webhook/paystack
   ```
3. **Configure webhook secret** in your `.env`:
   ```env
   BILLING_PAYSTACK_WEBHOOK_SECRET=your_webhook_secret_from_paystack
   ```

### Option 3: Other Tunneling Services

- **Cloudflare Tunnel** (free, permanent)
- **localtunnel** (free, temporary)
- **serveo** (free, SSH-based)

## 🔧 Paystack Webhook Configuration

### Step 1: Get Webhook Secret from Paystack

1. Log in to [Paystack Dashboard](https://dashboard.paystack.com)
2. Go to **Settings** → **Webhooks**
3. Click **Add Webhook URL**
4. Enter your webhook URL (ngrok URL for dev, or production URL)
5. Copy the **Webhook Secret** (starts with `whsec_` or similar)

### Step 2: Configure Your Backend

Add to your `.env` file:

```env
# Paystack Configuration
BILLING_PAYSTACK_SECRET_KEY=sk_test_...  # Your secret key
BILLING_PAYSTACK_PUBLIC_KEY=pk_test_...  # Your public key
BILLING_PAYSTACK_WEBHOOK_SECRET=whsec_...  # Webhook secret from Paystack
BILLING_WEBHOOK_BASE_URL=https://your-domain.com  # Your public URL
```

### Step 3: Test Webhook

1. Make a test payment
2. Check Paystack dashboard → **Webhooks** → **Events** to see if webhook was sent
3. Check your backend logs to see if webhook was received
4. Verify subscription was activated in your database

## 📋 Webhook Events Handled

Your backend handles these Paystack webhook events:

- ✅ `charge.success` - Payment successful, activates subscription
- ✅ `subscription.create` - Subscription created
- ✅ `subscription.disable` - Subscription cancelled
- ✅ `transfer.success` - Transfer completed

## 🔒 Security

- Webhook signature verification is enabled
- Only webhooks with valid signatures are processed
- Invalid signatures are rejected

## 🚨 Troubleshooting

### Webhook Not Received

1. **Check Paystack Dashboard** → Webhooks → Events
   - See if webhook was sent
   - Check response status
   
2. **Check Your Backend Logs**
   - Look for webhook requests
   - Check for errors

3. **Verify URL is Correct**
   - Must be HTTPS (not HTTP)
   - Must be publicly accessible
   - Must include full path: `/api/v1/billing/webhook/paystack`

4. **Check Firewall/Security**
   - Ensure port 8000 is accessible (if using ngrok, this is handled)
   - Check if your server blocks incoming requests

### Webhook Received But Subscription Not Activated

1. **Check Database Connection**
   - Ensure Supabase/PostgreSQL is accessible
   - Check connection credentials

2. **Check Webhook Handler Logs**
   - Look for errors in `backend/core/billing/paystack_integration.py`
   - Check if subscription_id is found in metadata

3. **Verify Metadata**
   - Ensure `subscription_id` is in webhook metadata
   - Check if subscription exists in database

## 📝 Summary

- ❌ **localhost:3000 won't work** - Paystack can't reach it
- ✅ **Use ngrok for development** - Creates public tunnel
- ✅ **Use real domain for production** - Deploy to GCP/cloud
- ✅ **Configure webhook secret** - Get from Paystack dashboard
- ✅ **Test thoroughly** - Verify webhooks are received and processed

---

**For Development:** Use ngrok to tunnel localhost → public URL  
**For Production:** Deploy to GCP and use your domain URL

