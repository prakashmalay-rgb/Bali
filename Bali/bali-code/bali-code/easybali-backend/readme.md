# EASY-BALI Backend

The official backend for the [EASY-BALI](https://bali-zeta.vercel.app/) ecosystem. Built with **FastAPI**, **MongoDB**, and **Pinecone RAG** to provide a seamless, AI-driven guest experience.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- MongoDB (Local or Atlas)
- AWS Account (S3 for file storage)
- Meta Developer Account (WhatsApp Cloud API)

### Installation

1. **Clone the repo**: `git clone <repo-url>`
2. **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

3. **Configure Environment**:
    - Copy `.env.template` to `.env`
    - Populate keys for `MONGO_URII`, `OPENAI_API_KEY`, `AWS_ACCESS_KEY`, etc.
4. **Run Locally**:

    ```bash
    uvicorn main:app --reload
    ```

---

## 📁 Repository Structure

```text
easybali-backend/
├── app/
│   ├── db/             # MongoDB session & index management
│   ├── routes/         # API endpoints (WhatsApp, Chatbot, Onboarding)
│   ├── services/       # Core logic (OpenAI, RAG, Message Queue)
│   ├── settings/       # Pydantic configuration settings
│   ├── utils/          # S3, Crypto, and Formatting helpers
│   └── main.py         # Sub-app entrypoint
├── main.py             # Root production entrypoint (Background workers)
├── Dockerfile          # Container configuration
└── requirements.txt    # Dependency list
```

---

## 🛠 Key Features

- **Multi-tenant WhatsApp Bot**: Personalized concierge for multiple villas.
- **RAG Engine**: Integration with Pinecone for villa-specific FAQs and local guides.
- **Message Reliability**: Persistent MongoDB queue with automated retry logic.
- **Secure File Submission**: Encrypted S3 uploads for sensitive guest docs (Passports).
- **Onboarding System**: Automated QR code generation and villa management.

---

## 📡 Core API Endpoints

- `GET /onboarding/dashboard`: Admin overview of all onboarded villas.
- `POST /whatsapp-flow`: Webhook for Meta Flow interactions.
- `POST /chatbot/booking-history/{user_id}`: Retrieves guest transaction history.
- `POST /onboarding/generate-qr`: Generates unique scan links for new villas.

---

## 🔒 Security & Compliance

- **SSE-S3 Encryption**: All uploaded files are encrypted at rest using AES-256.
- **JWT Auth**: Secured dashboard access for villa staff.
- **Compliance Logging**: Every access attempt to PII is logged in `compliance_logs`.

---

## 🚢 Deployment

Target Environment: **Render.com** (Docker runtime).

- Root directory: `easybali-backend/`
- Command: `uvicorn main:app --host 0.0.0.0 --port 8000`
