# 🎯 Complete Flow Testing Guide
## Service Inquiry → Payment → Notifications

### 🌐 **Current Status: BOTH SERVICES RUNNING**
- **Frontend**: `http://localhost:5173` ✅
- **Backend**: `http://localhost:8000` ✅
- **API Docs**: `http://localhost:8000/docs` ✅

---

## 🧪 **Testing the Complete Flow**

### **Step 1: Service Discovery**
```bash
# Get all categories
curl "http://localhost:8000/services/categories"

# Get services in a category
curl "http://localhost:8000/services/list?category=Airport%20Transfer"

# Get specific service details
curl "http://localhost:8000/services/Airport%20Transfer%20-%20Ngurah%20Rai"
```

### **Step 2: Create Service Inquiry**
```bash
# Create inquiry without promo
curl -X POST "http://localhost:8000/services/inquire" \
-H "Content-Type: application/json" \
-d '{
  "service_name": "Airport Transfer - Ngurah Rai",
  "date": "2024-03-02",
  "time": "14:00",
  "sender_id": "+628123456789"
}'

# Create inquiry WITH promo
curl -X POST "http://localhost:8000/services/inquire" \
-H "Content-Type: application/json" \
-d '{
  "service_name": "Airport Transfer - Ngurah Rai",
  "date": "2024-03-02",
  "time": "14:00", 
  "sender_id": "+628123456789",
  "promo_code": "TEST20"
}'
```

### **Step 3: Provider Confirmation**
```bash
# Provider confirms the request
curl -X POST "http://localhost:8000/services/provider-response" \
-H "Content-Type: application/json" \
-d '{
  "order_number": "ORD20240301140000",
  "provider_id": "SP001",
  "response": "confirm"
}'
```

### **Step 4: Check Inquiry Status**
```bash
# Check order status
curl "http://localhost:8000/services/inquiry-status/ORD20240301140000"
```

---

## 📱 **Frontend Testing Flow**

### **1. Browse Services**
1. Visit: `http://localhost:5173`
2. Navigate to: Services/Bookings
3. Select: "Order Services"
4. Browse categories and services

### **2. Make Selection**
1. Choose: "Airport Transfer" 
2. Select: "Airport Transfer - Ngurah Rai"
3. Pick: Date and Time
4. Enter: WhatsApp number
5. Apply: Promo code (TEST20 for 20% off)

### **3. Complete Inquiry**
1. Submit: Service request
2. Receive: Order confirmation
3. Get: Payment link
4. See: Discount applied

---

## 💳 **Xendit Payment Testing**

### **Test Payment Flow**
1. **Get Payment URL**: From API response
2. **Visit Payment Link**: Mock Xendit checkout
3. **Test Cards**:
   - Success: `4811111111111114`
   - Fail: `4000000000000002`
4. **Verify Discount**: IDR 400,000 (20% off 500,000)

### **Webhook Testing**
```bash
# Simulate successful payment
curl -X POST "http://localhost:8000/webhook/xendit-payment" \
-H "Content-Type: application/json" \
-d '{
  "id": "inv_test123",
  "external_id": "booking_ORD20240301140000_1234567890",
  "status": "PAID",
  "amount": 400000,
  "payment_method": "CREDIT_CARD"
}'
```

---

## 📊 **Expected Results**

### **Service Inquiry Response**
```json
{
  "success": true,
  "order": {
    "order_number": "ORD20240301140000",
    "service_name": "Airport Transfer - Ngurah Rai",
    "price": "IDR 400000",
    "status": "pending_payment"
  },
  "payment": {
    "payment_url": "https://checkout.xendit.co/test/ORD20240301140000",
    "invoice_id": "inv_ORD20240301140000",
    "amount": 400000
  }
}
```

### **Provider Notification**
- WhatsApp message sent to service providers
- Message includes: Service details, time, customer info
- Reply format: "CONFIRM {order_number}"

### **Payment Completion**
- Order status: "payment_completed"
- Promo usage: Incremented by 1
- Notifications sent to: Customer, Villa, Provider, Easy-Bali

---

## 🔍 **Verification Checklist**

### **Frontend**
- [ ] Service categories load correctly
- [ ] Service details display properly
- [ ] Form validation works
- [ ] Promo codes apply discounts
- [ ] Payment links generate
- [ ] Status updates show

### **Backend**
- [ ] Categories endpoint works
- [ ] Service listing works
- [ ] Inquiry creation works
- [ ] Promo discounts apply
- [ ] Provider notifications send
- [ ] Payment webhooks process
- [ ] Status updates work

### **Integration**
- [ ] Frontend ↔ Backend communication
- [ ] Google Sheets data integration
- [ ] Xendit payment generation
- [ ] WhatsApp notifications
- [ ] Database updates

---

## 🚨 **Troubleshooting**

### **Common Issues**
1. **Service Not Found**: Check service name spelling
2. **Payment Fails**: Verify Xendit test mode
3. **No Discount**: Check promo code is active
4. **No Notification**: Check WhatsApp integration
5. **Status Not Updating**: Check webhook processing

### **Debug Commands**
```bash
# Check backend logs
curl "http://localhost:8000/health"

# Test specific endpoint
curl "http://localhost:8000/services/categories"

# Verify promo codes
curl "http://localhost:8000/promos/list"
```

---

## 🎯 **Success Criteria**

### **Complete Flow Working When:**
1. ✅ User can browse services from Google Sheets data
2. ✅ User can select service and make inquiry
3. ✅ System generates payment link with promo discounts
4. ✅ Providers receive notification and can confirm
5. ✅ Customer receives payment link after confirmation
6. ✅ Payment processing works with Xendit
7. ✅ All parties receive confirmation after payment
8. ✅ Analytics track all activities

---

## 🚀 **Ready for Production**

### **Before Deploying:**
- [ ] All test scenarios pass
- [ ] Real Google Sheets integration working
- [ ] Real Xendit API keys configured
- [ ] WhatsApp notifications verified
- [ ] Database operations stable

### **Production URLs:**
- **Frontend**: Your Vercel URL
- **Backend**: Your Render URL
- **Webhooks**: Updated to production URLs

---

**🎉 The complete booking and payment flow is now testable!**

Start with: `http://localhost:5173` and follow the flow through to payment completion! 🚀
