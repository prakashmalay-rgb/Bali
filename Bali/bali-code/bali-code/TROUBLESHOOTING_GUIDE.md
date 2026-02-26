# EASY-BALI Troubleshooting Guide

Common issues and their resolutions for the EASY-BALI Guest Concierge system.

---

## 🤖 Chatbot Issues

### "AI is having trouble responding"

- **Cause**: OpenAI API limit reached or invalid API key.
- **Fix**: Check `OPENAI_API_KEY` in backend `.env` and verify usage limits on [OpenAI Dashboard](https://platform.openai.com/usage).

### "Vector search failed" / Inaccurate FAQ answers

- **Cause**: Pinecone index is empty or improperly formatted.
- **Fix**: Run the ingestion script:

  ```bash
  python ingest_faqs.py
  ```

---

## 📱 WhatsApp & Messaging

### Messages not sending

- **Cause**: WhatsApp Cloud API token expired or Meta App ID mismatch.
- **Fix**: Verify `WHATSAPP_TOKEN` in settings. Check the `whatsapp_message_queue` collection in MongoDB to see if messages are stuck with errors.

### Latency is high (>5s)

- **Cause**: MongoDB connection lag or slow OpenAI response.
- **Fix**: Check `analytics_latency` collection to identify which step (Retrieval, Generation, or Sending) is slow.

---

## 🛂 Passport & File Uploads

### "Upload failed" in UI

- **Cause**: File size > 5MB or invalid file type.
- **Fix**: Ensure the guest is uploading a JPG, PNG, or PDF. Check AWS S3 bucket permissions for `PutObject`.

### Passports not showing in Dashboard

- **Cause**: Database indexing issue.
- **Fix**: Run the index utility:

  ```bash
  python app/db/ensure_indexes.py
  ```

---

## 💳 Payments & Bookings

### Xendit links not generating

- **Cause**: Invalid `XENDIT_SECRET_KEY` or unsupported currency setup.
- **Fix**: Verify Xendit keys and ensure the `location_zone` passed in the request matches the pricing rules in Google Sheets.
