from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sqlite3
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = FastAPI(title="Fizza Portfolio API")

# CORS - Allow your React frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
def init_db():
    conn = sqlite3.connect("messages.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Request Model
class ContactForm(BaseModel):
    name: str
    email: EmailStr
    message: str

# Function to send email
def send_email(name: str, user_email: str, message: str):
    try:
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = "fizzafaisal07@gmail.com"
        sender_password = os.getenv("GMAIL_APP_PASSWORD")
        
        if not sender_password:
            print("⚠️ No password found. Email not sent.")
            return False
        
        # Create email
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = sender_email  # Send to yourself
        msg["Subject"] = f"📧 Portfolio Message from {name}"
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #a855f7;">✨ New message from your portfolio!</h2>
            <p><strong>Name:</strong> {name}</p>
            <p><strong>Email:</strong> {user_email}</p>
            <p><strong>Message:</strong></p>
            <p style="background-color: #f0f0f0; padding: 15px; border-radius: 8px;">{message}</p>
            <hr>
            <p style="color: #666;">Reply directly to: <a href="mailto:{user_email}">{user_email}</a></p>
            <p><small>Sent from your portfolio website</small></p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, "html"))
        
        # Send
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

@app.post("/api/contact")
async def submit_contact(form: ContactForm, background_tasks: BackgroundTasks):
    try:
        conn = sqlite3.connect("messages.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO contacts (name, email, message) VALUES (?, ?, ?)",
            (form.name, form.email, form.message)
        )

        conn.commit()
        conn.close()

        background_tasks.add_task(
            send_email,
            form.name,
            form.email,
            form.message
        )

        return {
            "success": True,
            "message": "Message sent successfully!"
        }

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        

@app.get("/api/health")
async def health():
    return {"status": "healthy", "time": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)