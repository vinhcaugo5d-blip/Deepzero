from fastapi import FastAPI, HTTPException, Request, Depends
from pydantic import BaseModel, EmailStr
import sqlite3
import hashlib

app = FastAPI(title="DeepZero Auth Node")

# Khởi tạo Database SQLite lưu tài khoản
def init_db():
    conn = sqlite3.connect("deepzero_users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT,
            ip_address TEXT UNIQUE
        )
    """)
    conn.commit()
    conn.close()

init_db()

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

@app.post("/register")
def register_user(req: RegisterRequest, request: Request):
    # Lấy địa chỉ IP thực tế của người dùng gọi lên
    client_ip = request.client.host
    
    # Kiểm tra xem IP này đã đăng ký tài khoản nào trước đó chưa
    conn = sqlite3.connect("deepzero_users.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE ip_address = ?", (client_ip,))
    existing_ip = cursor.fetchone()
    if existing_ip:
        conn.close()
        raise HTTPException(
            status_code=403, 
            detail="Mỗi địa chỉ IP chỉ được phép tạo duy nhất 1 tài khoản trên DeepZero!"
        )
    
    # Kiểm tra email đã tồn tại chưa
    cursor.execute("SELECT * FROM users WHERE email = ?", (req.email,))
    existing_email = cursor.fetchone()
    if existing_email:
        conn.close()
        raise HTTPException(
            status_code=400, 
            detail="Email này đã được sử dụng."
        )
    
    # Lưu tài khoản mới kèm IP vào Database
    hashed_pwd = hash_password(req.password)
    try:
        cursor.execute(
            "INSERT INTO users (email, password, ip_address) VALUES (?, ?, ?)", 
            (req.email, hashed_pwd, client_ip)
        )
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))
    
    conn.close()
    return {
        "status": "success", 
        "message": "Đăng ký tài khoản DeepZero thành công!", 
        "registered_ip": client_ip
    }
