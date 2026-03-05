# 🧪 Local Testing Guide - M1/M2 Features

## 📋 **Current Status: READY FOR TESTING**

### ✅ **Completed Features**
- **M1 Core System**: 100% Complete
- **M2 Additional Features**: 100% Complete
  - ✅ Promo Code System (Backend + Frontend)
  - ✅ Voice Note Transcription
  - ✅ Compliance Logging
  - ✅ Analytics Dashboard
  - ✅ Quality Gates & Testing

---

## 🚀 **Quick Start - Local Testing**

### **1. Start Backend**
```bash
cd easybali-backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### **2. Start Frontend**
```bash
cd bali-frontend
npm run dev
```

### **3. Run Quality Gates**
```bash
cd bali-code/bali-code
python quality_gates.py
```

---

## 🧪 **Testing Checklist**

### **🔧 Basic Functionality**
- [ ] Backend starts on http://localhost:8000
- [ ] Frontend starts on http://localhost:5173
- [ ] Health check: http://localhost:8000/health
- [ ] Database connection working

### **🎫 Promo Code Testing**
1. **Create Promo Code**
   - Go to: http://localhost:5173/dashboard/promo-management
   - Create test promo: `TEST20` (20% percentage)
   - Set usage limit: 5
   - Set expiry: +30 days

2. **Test Promo Validation**
   ```bash
   curl -X POST "http://localhost:8000/promos/create" \
   -H "Content-Type: application/json" \
   -d '{
     "code": "TEST20",
     "type": "percentage", 
     "value": 20.0,
     "usage_limit": 5
   }'
   ```

3. **Verify in Database**
   ```bash
   # Check MongoDB for promo codes
   # Collection: promo_codes
   # Should see your TEST20 promo
   ```

### **💳 Xendit Payment Testing**

#### **Test Environment Setup**
1. **Get Xendit Test Keys**
   - Go to Xendit Dashboard
   - Switch to **Test Mode** (toggle top-right)
   - Get your **Test Secret Key** (starts with `xnd_development_`)

2. **Update Environment**
   ```bash
   # In easybali-backend/.env
   XENDIT_SECRET_KEY=xnd_development_YOUR_TEST_KEY
   ```

#### **Test Payment Flow**
1. **Create Test Order**
   ```bash
   curl -X POST "http://localhost:8000/test/create-order" \
   -H "Content-Type: application/json" \
   -d '{
     "service_name": "Airport Transfer",
     "price": "IDR 500000",
     "promo_code": "TEST20"
   }'
   ```

2. **Verify Discount Applied**
   - Original: IDR 500,000
   - With 20% discount: IDR 400,000
   - Check Xendit invoice amount

3. **Test Payment Methods**
   - Use Xendit test cards:
     - **Success**: `4811111111111114`
     - **Fail**: `4000000000000002`
   - Or use **Virtual Account** (BCA, BNI, etc.)

4. **Test Webhook**
   ```bash
   # Use ngrok to expose localhost
   ngrok http 8000
   
   # Update webhook URL in Xendit dashboard:
   # https://your-ngrok-url.ngrok.io/webhook/xendit-payment
   ```

### **🎤 Voice Transcription Testing**
```bash
# Upload audio file for transcription
curl -X POST "http://localhost:8000/voice/transcribe" \
-F "file=@test_voice.ogg" \
-F "user_id=test_user"
```

### **📊 Analytics Testing**
```bash
# Get villa performance
curl "http://localhost:8000/analytics/villa-performance?days=30"

# Get service analytics  
curl "http://localhost:8000/analytics/service-analytics?days=30"

# Get revenue analytics (admin only)
curl "http://localhost:8000/analytics/revenue?days=30"
```

### **🔒 Compliance Testing**
```bash
# Get compliance logs
curl "http://localhost:8000/compliance/logs?limit=10"

# Test compliance logging
curl -X POST "http://localhost:8000/compliance/log-test?action=test_access"
```

---

## 🧪 **Unit Testing**

### **Run Promo Code Tests**
```bash
cd easybali-backend
python test_promo_integration.py -v
```

### **Expected Test Results**
- ✅ Valid promo code validation
- ✅ Invalid promo code rejection  
- ✅ Expired promo code handling
- ✅ Usage limit enforcement
- ✅ Fixed vs percentage discounts
- ✅ Case insensitive codes

---

## 🔍 **Debugging Tools**

### **Check Backend Logs**
```bash
# Look for these key log messages:
# - "Promo code TEST20 applied: Applied 20% discount"
# - "Payment distribution successful for order"
# - "Voice transcription completed"
# - "PII access logged"
```

### **Database Verification**
```bash
# Check these collections:
# - promo_codes (should have your test promos)
# - orders (should have payment data with discounts)
# - compliance_logs (should track PII access)
```

### **Frontend Verification**
- **Promo Management**: http://localhost:5173/dashboard/promo-management
- **Dashboard**: http://localhost:5173/dashboard
- **Chatbot**: Test promo code application in chat

---

## ⚠️ **Common Issues & Solutions**

### **Issue: Promo code not working**
**Solution**: 
1. Check promo exists in MongoDB
2. Verify `active: true`
3. Check expiry date
4. Verify usage limit not reached

### **Issue: Xendit payment failing**
**Solution**:
1. Ensure using **Test Mode**
2. Check API key format (`xnd_development_`)
3. Verify webhook URL is accessible
4. Check bank details configuration

### **Issue: Voice transcription failing**
**Solution**:
1. Check OpenAI API key
2. Verify audio format (MP3, WAV, M4A, OGG)
3. Check file size (<25MB)
4. Ensure internet connectivity

---

## 🚀 **Ready for Production?**

### **Pre-Deployment Checklist**
- [ ] All quality gates pass: `python quality_gates.py`
- [ ] Unit tests pass: `python test_promo_integration.py -v`
- [ ] Promo codes work end-to-end
- [ ] Xendit payments process correctly
- [ ] Voice transcriptions complete
- [ ] Analytics data displays properly
- [ ] Compliance logs are generated

### **Environment Variables Required**
```bash
# Backend (.env)
MONGO_URII=mongodb+srv://...
OPENAI_API_KEY=sk-proj-...
XENDIT_SECRET_KEY=xnd_development_...  # Change to xnd_production_ for live
AWS_ACCESS_KEY=...
AWS_SECRET_KEY=...
PINECONE_API_KEY=...

# Frontend (.env)
VITE_API_URL=http://localhost:8000  # Change to production URL
VITE_WA_PHONE_NUMBER=628123456789
```

---

## 🎯 **Production Deployment Steps**

### **1. Update Environment**
```bash
# Switch to production keys
XENDIT_SECRET_KEY=xnd_production_...
VITE_API_URL=https://your-backend-url.com
```

### **2. Git Push to Main**
```bash
git add .
git commit -m "M1/M2 Complete: Promo codes, voice transcription, analytics, compliance"
git push origin main
```

### **3. Vercel Deployment** (Automatic)
- Frontend will deploy automatically
- Monitor Vercel dashboard for deployment status

### **4. Render Deployment** (Manual)
- Go to Render dashboard
- Trigger manual deployment
- Monitor health checks

### **5. Post-Deployment Verification**
- Test production URLs
- Verify webhook endpoints
- Check database connectivity
- Monitor error logs

---

## 🆘 **Troubleshooting Support**

### **If Something Goes Wrong**
1. **Check Logs**: Backend and frontend logs
2. **Run Quality Gates**: `python quality_gates.py`
3. **Verify Environment**: All required variables set
4. **Test Database**: Connection and collections
5. **Rollback**: Git checkout to previous commit if needed

### **Get Help**
- Check this guide first
- Review error messages in logs
- Test each component individually
- Use the debugging tools provided

---

**🎉 You're ready to test! All M1/M2 features are implemented and waiting for your verification.**
