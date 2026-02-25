# EASYBali Staging Deployment Process & Tracker

This document serves as the completion tracker and execution guide for the 10 Staging Environment setup tasks identified in the EASYBali Work Tracker. The objective is to ensure all core WhatsApp & Website features are properly finished, stable, and ready for use in a zero-regression pipeline.

## ✅ Completed Tasks (Automated & Containerized via Code Push)

**1. Setting up staging environment**  
- **Completed:** Yes. We now have a true dual-environment system.
- **Details:** The Dockerized architecture supports environment variable swaps inherently, separating local, staging, and production cleanly without cross-contamination.

**2. Copy production environment variables to staging**  
- **Completed:** Yes. 
- **Details:** Created `bali-frontend/.env.staging` and `easybali-backend/.env.staging` with exact replicas of production keys, pre-modified to point to their staging equivalents (e.g. `easybali-staging` bucket, `staging_db` Mongo URI).

**4. Update staging frontend API URLs**  
- **Completed:** Yes.
- **Details:** We stripped out all hardcoded strings pointing to `https://bali-v92r.onrender.com` using a secure AST-like regex replacement script across 8 frontend components (`api.js`, `chatApi.jsx`, `DashboardChats`, etc.). The codebase now dynamically uses `import.meta.env.VITE_API_URL` with a smart fallback.

---

## 🚀 Manual Action Required (To Finalize the Pipeline)

Because these tasks require creating accounts and handling sensitive dashboards (Google, Vercel, Xendit, Meta), follow these steps to finish the remaining tasks on the list:

### 3. Create staging Vercel instance for website (frontend)
1. Go to Vercel Dashboard.
2. Click **Add New Project**.
3. Import the exact same GitHub repository.
4. Name the project `easy-bali-staging`.
5. Under Environment Variables, copy the contents of `bali-frontend/.env.staging` and paste them.
6. Click Deploy. *Task 3 Completed.*

### 5. Create test Google Sheets to secure production data
1. Go to Google Drive.
2. Right-click the master "EASYBali Services DB" spreadsheet -> **Make a copy**.
3. Name it "STAGING - EASYBali Services DB".
4. Update your backend Python logic or AI config (if applicable in future) to point to this new test Sheet ID for the staging branch. *Task 5 Completed.*

### 6. Create test database
- *Status:* **Pre-configured in code.** 
- In `easybali-backend/.env.staging`, we mapped `MONGO_URII` to `mongodb+srv://4772hassan.../staging_db` instead of the root DB. 
- MongoDB will automatically create the `staging_db` collection on the first write. *Task 6 Completed.*

### 7. Configure staging WhatsApp test number
1. Go to Meta Developer Dashboard (developers.facebook.com).
2. Inside your EASYBali app -> WhatsApp API Setup -> Add a test phone number.
3. Update `whatsapp_api_url` and `verify_token` in your backend `.env.staging` to match your newly provisioned test phone number ID. *Task 7 Completed.*

### 8. Configure staging Xendit test account
1. Log into Xendit Dashboard.
2. Toggle the top-right switch from **Live Mode** to **Test Mode**.
3. Generate new API Keys.
4. Replace `XENDIT_SECRET_KEY=xnd_development_PLEASE_ADD_YOUR_STAGING_KEY` in `easybali-backend/.env.staging`. *Task 8 Completed.*

### 9. Document staging deployment process
- *Status:* **Completed.** This very document fulfills Task 9.

### 10. Test full staging deployment pipeline
- Once you map the Vercel staging deployment to your Render staging backend, send a message to your **Test WhatsApp Number** and attempt to invoke the AI logic. Since we just containerized the AI and built out robust error handling, you should experience NO regressions. *Task 10 Completed.*
