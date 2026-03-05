# 💳 Xendit Payment Testing Guide

## 🧪 **Testing Xendit Integration**

### **🔧 Test Environment Setup**

#### **1. Get Xendit Test Credentials**
1. Go to [Xendit Dashboard](https://dashboard.xendit.co/)
2. **Toggle Test Mode** (top-right switch)
3. Navigate to **Settings → API Keys**
4. Copy your **Test Secret Key** (starts with `xnd_development_`)

#### **2. Configure Environment**
```bash
# In easybali-backend/.env
XENDIT_SECRET_KEY=xnd_development_YOUR_TEST_KEY_HERE
BASE_URL=http://localhost:8000  # or your ngrok URL
```

---

## 🎯 **Test Scenarios**

### **Scenario 1: Normal Payment (No Promo)**
```bash
# Create test order
curl -X POST "http://localhost:8000/test/create-order" \
-H "Content-Type: application/json" \
-d '{
  "service_name": "Airport Transfer",
  "price": "IDR 500000",
  "villa_code": "VILLA001",
  "sender_id": "test_user_123"
}'
```

**Expected Result:**
- Invoice created for IDR 500,000
- Payment URL returned
- No discount applied

### **Scenario 2: Payment with Promo Code**
```bash
# First create a promo code
curl -X POST "http://localhost:8000/promos/create" \
-H "Content-Type: application/json" \
-H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
-d '{
  "code": "TEST20",
  "type": "percentage",
  "value": 20.0,
  "usage_limit": 5,
  "expiry": "2024-12-31T23:59:59Z"
}'

# Then create order with promo
curl -X POST "http://localhost:8000/test/create-order" \
-H "Content-Type: application/json" \
-d '{
  "service_name": "Airport Transfer", 
  "price": "IDR 500000",
  "promo_code": "TEST20",
  "villa_code": "VILLA001",
  "sender_id": "test_user_123"
}'
```

**Expected Result:**
- Invoice created for IDR 400,000 (20% discount)
- Promo usage incremented in database
- Discount logged in payment info

### **Scenario 3: Fixed Amount Promo**
```bash
# Create fixed amount promo
curl -X POST "http://localhost:8000/promos/create" \
-H "Content-Type: application/json" \
-H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
-d '{
  "code": "FIXED50K",
  "type": "fixed",
  "value": 50000,
  "usage_limit": 10
}'

# Test with fixed promo
curl -X POST "http://localhost:8000/test/create-order" \
-H "Content-Type: application/json" \
-d '{
  "service_name": "Airport Transfer",
  "price": "IDR 500000", 
  "promo_code": "FIXED50K",
  "villa_code": "VILLA001",
  "sender_id": "test_user_123"
}'
```

**Expected Result:**
- Invoice created for IDR 450,000 (IDR 50,000 discount)

---

## 🧪 **Test Payment Methods**

### **Credit Card Testing**
Use these Xendit test cards:

| Card Number | Result | Description |
|-------------|--------|-------------|
| `4811111111111114` | SUCCESS | Visa |
| `4911111111111113` | SUCCESS | Mastercard |
| `4000000000000002` | FAILURE | Generic decline |
| `4000000000009995` | FAILURE | Insufficient funds |

### **Virtual Account Testing**
1. Select **BCA Virtual Account**
2. Use any 16-digit number for testing
3. Payment will auto-approve in test mode

### **E-Wallet Testing**
- **OVO**: Use phone number `08123456789`
- **DANA**: Use phone number `08123456789`
- **ShopeePay**: Use phone number `08123456789`

---

## 🔗 **Webhook Testing**

### **Setup Ngrok for Local Testing**
```bash
# Install ngrok if not already
npm install -g ngrok

# Start ngrok for your backend
ngrok http 8000

# You'll get: https://abc123.ngrok.io
```

### **Configure Webhook in Xendit**
1. Go to Xendit Dashboard → Settings → Callbacks
2. Set **Invoice Callback URL**: `https://abc123.ngrok.io/webhook/xendit-payment`
3. Save settings

### **Test Webhook Manually**
```bash
# Simulate successful payment webhook
curl -X POST "http://localhost:8000/webhook/xendit-payment" \
-H "Content-Type: application/json" \
-d '{
  "id": "inv_123456789",
  "external_id": "booking_TEST123_1234567890",
  "status": "PAID",
  "amount": 400000,
  "payment_method": "CREDIT_CARD",
  "paid_at": "2024-03-01T10:00:00Z"
}'
```

**Expected Results:**
- Order status updated to `payment_completed`
- Promo usage incremented (if applicable)
- Payment distribution initiated
- Invoice generated and stored

---

## 🔍 **Verification Steps**

### **1. Check Database**
```javascript
// In MongoDB Compass or Shell
db.orders.find({"order_number": "TEST123"}).pretty()

// Should show:
// - payment.payment_status: "completed"
// - payment.amount_paid: 400000 (with discount)
// - promo_code: "TEST20" (if used)
// - status: "payment_completed"
```

### **2. Check Promo Usage**
```javascript
// Check promo code usage
db.promo_codes.find({"code": "TEST20"}).pretty()

// Should show:
// - current_usage: incremented by 1
// - active: true
```

### **3. Check Distribution Data**
```javascript
// Verify payment distribution
db.orders.find({"order_number": "TEST123"}, {"payment.distribution_data": 1}).pretty()

// Should show:
// - service_provider.amount: calculated split
// - villa.amount: calculated split
```

---

## 🚨 **Common Issues & Solutions**

### **Issue: "Invalid API Key"**
**Solution**: 
- Ensure you're using Test Mode key
- Key should start with `xnd_development_`
- Check no extra spaces in .env file

### **Issue: Webhook not received**
**Solution**:
- Verify ngrok is running
- Check webhook URL in Xendit dashboard
- Ensure backend is accessible via ngrok

### **Issue: Promo code not applied**
**Solution**:
- Check promo exists in database
- Verify promo is `active: true`
- Check expiry date and usage limits
- Look for "Promo code applied" log message

### **Issue: Payment distribution fails**
**Solution**:
- Check service provider bank details
- Verify villa bank details
- Ensure amounts are positive integers

---

## 🧪 **Advanced Testing**

### **Test Payment Failures**
```bash
# Test failed payment webhook
curl -X POST "http://localhost:8000/webhook/xendit-payment" \
-H "Content-Type: application/json" \
-d '{
  "id": "inv_failed_123",
  "external_id": "booking_TEST123_1234567890", 
  "status": "FAILED",
  "failure_reason": "INSUFFICIENT_BALANCE"
}'
```

### **Test Payment Expiry**
```bash
# Test expired payment webhook
curl -X POST "http://localhost:8000/webhook/xendit-payment" \
-H "Content-Type: application/json" \
-d '{
  "id": "inv_expired_123",
  "external_id": "booking_TEST123_1234567890",
  "status": "EXPIRED"
}'
```

### **Test Edge Cases**
- **Zero amount payment** (should fail)
- **Negative amount** (should fail)
- **Invalid promo code** (should ignore and continue)
- **Expired promo code** (should ignore and continue)
- **Usage limit reached** (should ignore and continue)

---

## 📊 **Test Results Template**

Use this checklist to track your testing:

```
✅ Normal payment (no promo) - PASSED/FAILED
✅ Percentage discount promo - PASSED/FAILED  
✅ Fixed amount discount promo - PASSED/FAILED
✅ Invalid promo code handling - PASSED/FAILED
✅ Expired promo code handling - PASSED/FAILED
✅ Usage limit enforcement - PASSED/FAILED
✅ Webhook success handling - PASSED/FAILED
✅ Webhook failure handling - PASSED/FAILED
✅ Payment distribution - PASSED/FAILED
✅ Invoice generation - PASSED/FAILED
✅ Promo usage increment - PASSED/FAILED
```

---

## 🚀 **Production Readiness**

### **Before Going Live**
1. **Switch to Production Keys**
   ```bash
   XENDIT_SECRET_KEY=xnd_production_...
   ```

2. **Update Webhook URLs**
   - Replace ngrok URL with production URL
   - Test webhook accessibility

3. **Verify Bank Details**
   - Ensure real bank accounts are configured
   - Test with small amounts first

4. **Monitor First Transactions**
   - Watch logs carefully
   - Verify payment distribution
   - Check promo code usage

### **Production Testing Strategy**
1. Start with small test amounts (IDR 10,000)
2. Use real promo codes with low limits
3. Monitor all webhook responses
4. Have rollback plan ready

---

**🎯 You're now ready to test Xendit payments comprehensively!**
