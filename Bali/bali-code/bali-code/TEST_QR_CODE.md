# 📱 QR Code Testing Guide

## 🎯 **Current Flow Analysis**

### **Payment Link Timing: IMMEDIATE**
✅ **Current Implementation**: Payment link generated IMMEDIATELY after booking
✅ **No Provider Confirmation Required**: Payment link sent right away
✅ **Flow Matches Your Chart**: User books → Gets payment link → Pays → Providers notified

### **Expected Timeline:**
```
User Books Service → [0 seconds] → Payment Link Generated → User Pays → [Instant] → All Parties Notified
```

---

## 🧪 **Test the Current Flow**

### **Quick Test Command:**
```bash
curl -X POST http://localhost:8000/chatbot/create-booking-payment \
-H "Content-Type: application/json" \
-d '{
  "id": "test_booking",
  "title": "Airport Transfer - Ngurah Rai",
  "price": "IDR 500000",
  "user_id": "+628123456789",
  "location_zone": "VILLA001",
  "promo_code": "TEST20"
}'
```

### **Expected Response:**
```json
{
  "response": "🎉 **Booking Confirmed!**\n\n**Service**: Airport Transfer - Ngurah Rai\n**Location**: VILLA001\n**Date**: Selected Date\n**Time**: Selected Time\n\n💰 **Price**: IDR 400,000\n🎁 **Promo Applied**: Applied 20% discount\n💸 **You Saved**: IDR 100,000\n\n⏳ **Next Steps**:\n1. We'\''ve notified available service providers\n2. First provider to confirm gets your booking\n3. You'\''ll receive payment link once confirmed\n4. Complete payment for instant confirmation\n\n💳 **Payment Link**: [Click Here When Ready](https://checkout.xendit.co/test/ORD20240301140000)\n\n📱 **WhatsApp**: +628123456789 for support"
}
```

---

## 📱 **QR Code for Testing**

### **Test QR Code:**
```
📲 SCAN ME FOR EASYBALI BOOKING

URL: http://localhost:5173

This QR code will take you directly to the EASYBali chatbot where you can:
1. Order services from Google Sheets data
2. Apply promo codes for discounts
3. Get instant payment links
4. Complete booking immediately

Test the complete flow:
- Scan QR → Chatbot opens → Type "Order Services" → Select service → Get payment link
```

### **Generate Real QR Code:**
Use any QR code generator with this URL:
```
http://localhost:5173
```

---

## 🔍 **Troubleshooting Payment Link Issues**

### **If Payment Link Not Showing:**

#### **1. Check Backend Response:**
```bash
# Test the booking endpoint directly
curl -X POST http://localhost:8000/chatbot/create-booking-payment \
-H "Content-Type: application/json" \
-d '{
  "id": "debug_test",
  "title": "Airport Transfer - Ngurah Rai", 
  "price": "IDR 500000",
  "user_id": "+628123456789"
}'
```

#### **2. Check Frontend Integration:**
- Open browser developer tools (F12)
- Go to Network tab
- Make a booking request
- Check if `/chatbot/create-booking-payment` is called
- Verify response contains payment URL

#### **3. Check Xendit Configuration:**
```bash
# Check if Xendit is configured
curl http://localhost:8000/health
```

---

## 🧪 **Xendit Sandbox Testing**

### **Sandbox Mode Setup:**
1. **Go to Xendit Dashboard**
2. **Switch to Test Mode** (toggle top-right)
3. **Use Test Keys**: `xnd_development_...`
4. **Test Payment URLs**: Should work immediately

### **Test Payment Flow:**
1. **Get Payment Link**: From booking response
2. **Visit Link**: Should open Xendit test checkout
3. **Use Test Card**: `4811111111111114`
4. **Complete Payment**: Should succeed immediately

---

## 🎯 **Expected User Experience**

### **Ideal Flow:**
```
1. User scans QR code → Opens chatbot
2. User types "Order Services" → Sees categories
3. User selects service → Sees details and price
4. User enters details → Gets IMMEDIATE payment link
5. User clicks payment link → Opens Xendit checkout
6. User pays → Gets instant confirmation
7. All parties notified → Booking complete
```

### **Timing Expectations:**
- **Payment Link Generation**: < 2 seconds after booking
- **Payment Processing**: < 30 seconds
- **Confirmation Notifications**: < 5 seconds after payment
- **Total Booking Time**: < 1 minute

---

## 🚨 **If Issues Persist**

### **Debug Steps:**
1. **Check Backend Logs**: Look for Xendit errors
2. **Verify Service Data**: Ensure Google Sheets integration works
3. **Test Payment API**: Direct Xendit API call
4. **Check Frontend**: Verify API calls are made correctly

### **Common Issues:**
- **Xendit API Key**: Wrong or missing
- **Service Not Found**: Google Sheets data issue
- **Network Error**: Frontend-backend connection
- **Payment Link**: Generated but not displayed

---

## 🎊 **Success Indicators**

### **When Flow is Working:**
✅ QR code opens chatbot instantly
✅ Service categories load from Google Sheets
✅ Booking creates payment link immediately
✅ Payment link opens Xendit checkout
✅ Test card payments succeed
✅ Confirmations sent to all parties
✅ Total time < 1 minute

---

**🚀 The payment link should be generated IMMEDIATELY (within 2 seconds) after booking!**

**Test with the QR code and commands above to verify the complete flow works instantly!**
