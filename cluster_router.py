from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

app = FastAPI(title="DeepZero Cluster Router")

# Danh sách các Worker node đang hoạt động trong cụm của bạn
WORKER_NODES = [
    "http://localhost:8000"  # Địa chỉ worker hiện tại trên Colab
]

class ClusterRequest(BaseModel):
    prompt: str
    max_tokens: int = 300

@app.post("/route-generate")
def route_generate(req: ClusterRequest):
    # Thuật toán đơn giản chọn worker (Load balancing cơ bản)
    for worker_url in WORKER_NODES:
        try:
            response = requests.post(
                f"{worker_url}/generate",
                json={"prompt": req.prompt, "max_tokens": req.max_tokens},
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            continue
            
    raise HTTPException(status_code=503, detail="Tất cả các AI Worker trong cụm hiện đang bận hoặc ngoại tuyến.")
