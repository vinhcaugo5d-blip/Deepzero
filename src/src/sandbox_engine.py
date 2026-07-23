# src/sandbox_engine.py
import sys
import subprocess
import tempfile
import os
from typing import Dict, Any

class SelfHealingSandbox:
    def __init__(self, ai_engine):
        self.ai_engine = ai_engine

    def execute_and_verify(self, code_snippet: str, max_retries: int = 3) -> Dict[str, Any]:
        """Thực thi đoạn code Python trong môi trường cách ly và tự sửa lỗi nếu phát sinh bug."""
        current_code = code_snippet

        for attempt in range(1, max_retries + 1):
            # Tạo tệp tạm thời để thực thi kiểm thử
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp_file:
                tmp_file.write(current_code)
                tmp_path = tmp_file.name

            try:
                # Chạy thử code trong tiến trình riêng biệt
                result = subprocess.run(
                    [sys.executable, tmp_path],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if os.path.exists(tmp_path):
                    os.remove(tmp_path) # Dọn dẹp tệp tạm

                # Trường hợp code chạy thành công không có lỗi
                if result.returncode == 0:
                    return {
                        "status": "SUCCESS",
                        "attempts": attempt,
                        "verified_code": current_code,
                        "output": result.stdout.strip()
                    }

                # Trường hợp phát hiện lỗi -> Kích hoạt Tự sửa lỗi (Self-Healing)
                error_log = result.stderr.strip()
                print(f"[Sandbox] Lần thử {attempt} thất bại. Lỗi: {error_log}")
                
                if attempt < max_retries:
                    prompt_fix = f"""Đoạn code sau đây gặp lỗi khi vận hành:
```python
{current_code}
