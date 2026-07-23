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
                    # Ghép chuỗi an toàn bằng \n để không bị vỡ giao diện hiển thị
                    prompt_fix = (
                        "Đoạn code sau đây gặp lỗi khi vận hành:\n"
                        "```python\n"
                        f"{current_code}\n"
                        "```\n"
                        f"Lỗi hệ thống trả về:\n{error_log}\n\n"
                        "Hãy khắc phục và sửa lại toàn bộ đoạn code trên. "
                        "Chỉ trả về mã nguồn Python đã sửa trong khối ```python ... ```."
                    )
                    
                    fix_response = self.ai_engine.generate(
                        prompt=prompt_fix,
                        system_prompt="Bạn là trình tự sửa lỗi mã nguồn chuyên nghiệp."
                    )
                    
                    raw_text = fix_response["text"]
                    if "```python" in raw_text:
                        current_code = raw_text.split("```python")[1].split("```")[0].strip()
                    else:
                        current_code = raw_text

            except Exception as e:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                error_log = str(e)

        return {
            "status": "FAILED",
            "attempts": max_retries,
            "last_error": error_log,
            "code": current_code
        }
