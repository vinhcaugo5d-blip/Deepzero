from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import os
from huggingface_hub import InferenceClient

app = FastAPI(title="DeepZero AI Worker Node (Online API)")

print("🔥 Đang khởi động AI Worker qua API Online...")

# Sử dụng mô hình trực tiếp qua API của Hugging Face (hoặc bạn có thể thay bằng API key của mình)
# Khuyên dùng Qwen/Qwen2.5-7B-Instruct hoặc bản nhẹ hơn Qwen/Qwen2.5-1.5B-Instruct
MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"

# Khởi tạo InferenceClient (nếu có HF_TOKEN thì truyền vào, không thì dùng free tier)
client = InferenceClient(model=MODEL_ID)

print("🚀 AI Worker Online đã sẵn sàng nhận request!")

class AIRequest(BaseModel):
    prompt: str
    max_tokens: int = 300

@app.post("/generate")
def generate_text(req: AIRequest, authorization: str = Header(None)):
    try:
        messages = [{"role": "user", "content": req.prompt}]
        
        # Gọi API trực tuyến, không tốn RAM hay ổ đĩa máy chủ
        response = client.chat_completion(
            messages=messages,
            max_tokens=req.max_tokens,
            temperature=0.7,
            top_p=0.9
        )
        
        answer = response.choices[0].message.content
        
        return {
            "status": "success",
            "prompt": req.prompt,
            "response": answer.strip()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
