
# 🏥 Clinic Appointment Booking Chatbot  

An intelligent chatbot built with **FastAPI** (backend) and **Streamlit** (frontend) that allows patients to book clinical appointments easily.  
The chatbot understands natural language, extracts key details (name, age, doctor, date, time), and stores appointments in Google Sheets.  

---

## 📂 Project Structure
   ```
   
   clinic\_chatbot/
   │
   ├── app/
   │   ├── chains.py                # LangChain / Groq-based conversation logic
   │   ├── extractor.py             # Entity extraction (name, doctor, date, time)
   │   ├── main.py                  # FastAPI entrypoint
   │   ├── models.py                 # Pydantic models
   │   ├── sheets.py                 # Google Sheets integration
   │   ├── utils.py                  # Helper functions
   │   └── data/clinic\_data.json     # Example dataset
   │
   ├── frontend/
   │   └── app.py                    # Streamlit interface
   │
   ├── requirements.txt
   ├── .env.example                  # Environment variables template
   └── README.md
   
   ````

---

## 🚀 Features
- Book appointments via natural conversation.  
- Extracts patient details: **Name, Age, Doctor, Date, Time**.  
- Saves confirmed bookings into **Google Sheets**.  
- REST API backend using **FastAPI**.  
- Simple and interactive **Streamlit UI** frontend.  
- Modular design for easy extension.  

---

## 🛠️ Tech Stack
- **Backend:** FastAPI, Pydantic  
- **Frontend:** Streamlit  
- **NLP / AI:** Groq API + LangChain  
- **Database:** Google Sheets API  
- **Others:** Python-dotenv for env management  

---

## 🔑 Environment Variables Setup

This project uses a `.env` file to store sensitive API keys and credentials.  
For security, the real `.env` is ignored. Instead, we provide `.env.example`.

### Steps:
1. Copy the example:
   ```bash
   cp .env.example .env
   ````

2. Edit `.env` with your actual keys:

   ```env
   GROQ_API_KEY=your_real_groq_api_key_here
   GOOGLE_APPLICATION_CREDENTIALS=app/credentials/service-account.json
   ```

   * `GROQ_API_KEY` → Your Groq API key
   * `GOOGLE_APPLICATION_CREDENTIALS` → Path to your Google Cloud Service Account JSON key

3. Do **not** commit `.env` to GitHub.

---

## ⚙️ Installation & Setup

1. Clone the repo:

   ```bash
   git clone https://github.com/laibaabbas/Clinic-Appointment-Booking-chatbot.git
   cd Clinic-Appointment-Booking-chatbot
   ```

2. Create a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate   # macOS/Linux
   venv\Scripts\activate      # Windows
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

---

## ▶️ Running the Project

### 1. Run FastAPI backend

```bash
uvicorn app.main:app --reload
```

* API will be available at: `http://127.0.0.1:8000`
* Interactive docs: `http://127.0.0.1:8000/docs`

### 2. Run Streamlit frontend

```bash
streamlit run frontend/app.py
```

* Open the UI in your browser: `http://localhost:8501`

---

## 📊 Example Usage

User:

```
My name is Fatima, I’m 23, I want to book with Dr. Raza on 27 Aug at 3pm
```

System:

```
Hello Fatima,
Your appointment has been booked ✅
Doctor: Dr. Raza
Date: 27 August
Time: 3:00 PM
```

---

## 🛡️ Security Notes

* `.env` and service account keys must **never** be pushed to GitHub.
* Regenerate API keys if they were accidentally exposed.
* For deployment, use **environment variables** instead of `.env` files.

---

## ✨ Future Improvements

* Add authentication for patients.
* Email/SMS notifications for appointments.
* Better error handling & validation.
* Multi-language support.

---

## 👩‍💻 Author

Developed by **Laiba Abbas**
📧 [abbaslaiba695@gmail.com](mailto:abbaslaiba695@gmail.com)

```


