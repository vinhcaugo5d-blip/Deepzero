class SelfHealerAgent:
    def __init__(self, client):
        self.client = client

    def fix_code_error(self, faulty_code: str, error_message: str) -> str:
        """Tự động nhận diện lỗi từ traceback và yêu cầu AI vá lỗi"""
        prompt = f"""
        Đoạn mã sau đang gặp lỗi:
        ```python
        {faulty_code}
        ```
        Thông báo lỗi (Traceback):
        {error_message}
        
        Hãy phân tích nguyên nhân và viết lại toàn bộ đoạn mã đã được sửa lỗi một cách tối ưu nhất. Chỉ trả về code Python nằm trong khối code markdown.
        """
        
        messages = [{"role": "user", "content": prompt}]
        response = self.client.chat_completion(messages=messages, max_tokens=600)
        return response.choices[0].message.content.strip()
