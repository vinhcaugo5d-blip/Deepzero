# src/core_engine.py
import os
import time
from typing import Optional, Dict, Any

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

class LocalAIEngine:
    def __init__(self, model_path: str, n_ctx: int = 8192, n_threads: int = 8, n_gpu_layers: int = -1):
        """
        Khởi tạo Lõi AI chạy trên tham số mở (định dạng GGUF).
        :param model_path: Đường dẫn tới file trọng số .gguf
        :param n_ctx: Cửa sổ ngữ cảnh (Context Window)
        :param n_threads: Số nhân CPU dùng cho tính toán ma trận
        :param n_gpu_layers: Số layer đẩy lên GPU (-1 = đẩy tối đa nếu có GPU)
        """
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_threads = n_threads
        self.n_gpu_layers = n_gpu_layers
        self.model: Optional[Any] = None

        self._load_model()

    def _load_model(self):
        if Llama is None:
            raise ImportError("Thư viện 'llama-cpp-python' chưa được cài đặt.")

        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Không tìm thấy tệp tham số mô hình tại: {self.model_path}")

        print(f"[DeepZero Core] Đang nạp mô hình từ {self.model_path}...")
        start_time = time.time()
        
        # Nạp trọng số mô hình vào bộ nhớ
        self.model = Llama(
            model_path=self.model_path,
            n_ctx=self.n_ctx,
            n_threads=self.n_threads,
            n_gpu_layers=self.n_gpu_layers,
            verbose=False
        )
        print(f"[DeepZero Core] Nạp thành công trong {time.time() - start_time:.2f} giây.")

    def generate(self, prompt: str, system_prompt: str = "", max_tokens: int = 2048, temperature: float = 0.2) -> Dict[str, Any]:
        """
        Tạo phản hồi từ mô hình với tham số tối ưu hóa.
        """
        if not self.model:
            raise RuntimeError("Mô hình chưa được nạp thành công.")

        # Định dạng Prompt chuẩn ChatML
        formatted_prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"

        start_time = time.time()
        output = self.model(
            formatted_prompt,
            max_tokens=max_tokens,
            stop=["<|im_end|>"],
            echo=False,
            temperature=temperature
        )
        elapsed = time.time() - start_time

        response_text = output["choices"][0]["text"].strip()
        tokens_used = output.get("usage", {}).get("total_tokens", 0)

        return {
            "text": response_text,
            "tokens_used": tokens_used,
            "latency_seconds": round(elapsed, 2)
        }
