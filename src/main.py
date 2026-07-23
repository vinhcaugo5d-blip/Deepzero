# main.py
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Nạp các module đã viết ở Tệp 1, Tệp 2 và Tệp 3
from src.core_engine import LocalAIEngine
from src.sandbox_engine import SelfHealingSandbox
from src.cluster_router import MultiServerRouter

app = FastAPI(title="DeepZero Autonomous AI Engine")

# Đường dẫn mặc định tới file tham số mô hình (.gguf)
MODEL_PATH = os.getenv("MODEL_PATH", "./models/qwen2.5-coder-7b-instruct-q4_k_m.gguf")

# Khởi tạo các thành phần cốt lõi của hệ thống
ai_core = LocalAIEngine(model_path=MODEL_PATH)
sandbox = SelfHealingSandbox(ai_engine=ai_core)
router = MultiServerRouter()

# Định dạng dữ liệu yêu cầu gửi đến API
class CodeExecutionRequest(BaseModel):
    code: str

class ChatPromptRequest(BaseModel):
    prompt: str
    system_prompt: str = ""

@app.get("/health")
def health_check():
    """Endpoint kiểm tra trạng thái hoạt động của máy chủ."""
    return {"status": "ok", "service": "DeepZero Engine Running"}

@app.post("/api/chat")
def chat_endpoint(req: ChatPromptRequest):
    """Endpoint xử lý trò chuyện và phản hồi từ AI."""
    return ai_core.generate(prompt=req.prompt, system_prompt=req.system_prompt)

@app.post("/api/run-and-heal")
def run_and_heal_code(req: CodeExecutionRequest):
    """Endpoint chạy thử code và tự sửa lỗi nếu phát sinh bug."""
    return sandbox.execute_and_verify(req.code)

if __name__ == "__main__":
    import uvicorn
    # Khởi chạy server trên cổng 7860 (chuẩn của Hugging Face Spaces)
    uvicorn.run(app, host="0.0.0.0", port=7860)
