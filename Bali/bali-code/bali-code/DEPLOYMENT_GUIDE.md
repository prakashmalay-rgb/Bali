# EASY-BALI Deployment Guide

This document outlines the standard procedure for deploying the EASY-BALI ecosystem to production and staging environments.

## 🏗 System Architecture

- **Frontend**: React + Vite (Deployed on Vercel)
- **Backend**: FastAPI + Docker (Deployed on Render.com)
- **Database**: MongoDB Atlas (Transactional) + Pinecone (Vector Search)
- **Storage**: AWS S3 (Encrypted at rest for Passports)

---

## 🚀 Backend Deployment (Render)

### 1. Root Directory Setup

Render must be configured with a custom **Root Directory** because of the nested project structure:

- Set Root Directory to: `easybali-backend/`

### 2. Docker Configuration

- **Runtime**: Docker
- **Build Command**: Automatically detected from `Dockerfile`
- **Port**: Ensure Render is listening on port `8000`

### 3. Environment Variables

Ensure the following are set in the Render Dashboard:

- `MONGO_URII`: Your MongoDB connection string.
- `OPENAI_API_KEY`: API key for GPT-4/Retrieval.
- `AWS_ACCESS_KEY` / `AWS_SECRET_KEY`: Credentials for S3.
- `PINECONE_API_KEY`: For FAQ retrieval.

---

## 🌐 Frontend Deployment (Vercel)

### 1. Build Settings

- **Framework Preset**: Vite
- **Build Command**: `npm run build`
- **Output Directory**: `dist`

### 2. Environment Variables

- `VITE_API_URL`: Should point to your Render backend URL (e.g., `https://easybali-api.onrender.com`).
- `VITE_WA_PHONE_NUMBER`: The official WhatsApp number for guest contact.

---

## 🛠 Staging Environment

We maintain a duplicate environment for testing:

- **Frontend Staging**: `https://bali-zeta-staging.vercel.app`
- **Backend Staging**: `https://easybali-api-staging.onrender.com`
- **Database**: Uses a separate `easybali-staging` collection.

---

## ⛓ CI/CD Workflow

1. **Develop**: Create local branches for features.
2. **Verify**: Run `npm run lint` and `pytest` (backend).
3. **Deploy**: Pushing to the `main` branch triggers auto-deployments on both Vercel and Render.
