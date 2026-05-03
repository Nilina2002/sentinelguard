# 🚀 SentinelGuard Backend (FastAPI)

This is the backend service for SentinelGuard, built with FastAPI and MySQL.

---

## 🛠️ Tech Stack

- FastAPI
- SQLAlchemy / SQLModel
- Alembic (migrations)
- MySQL
- PyMySQL

---

## ⚙️ Backend Setup Instructions

### 1.
```bash
cd backend
```

### 2.
```bash
python -m venv venv
```

### 3.
```bash
venv\Scripts\activate      # Windows
source venv/bin/activate   # Linux / Mac
```

### 4.
```bash
pip install -r requirements.txt
```

### 5. Setup a MySQL Database locally named sentinel_db

### 6. Create .env file
```bash
DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/sentinel_db
```

### 7. Run Migrations (First Time Only)
```bash
alembic upgrade head
```

### 8. Start the Server
```bash
python run.py
```

### 9. After the first time, you only need to
```bash
venv\Scripts\activate
python run.py
```