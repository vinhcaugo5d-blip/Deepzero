import streamlit as st
import os
from huggingface_hub import InferenceClient
from datetime import datetime

# Cấu hình giao diện trang web
st.set_page_config(
    page_title="DeepZero AI Assistant", 
    page_icon="🤖", 
    layout="centered",
    initial_sidebar_state="auto"
)

# Giao diện tiêu đề chính
st.title("🤖 DeepZero AI Assistant (Online 24/7)")
st.markdown("*Hệ thống trợ lý ảo phát triển bởi DeepZero dựa trên nền tảng mô hình mã nguồn mở.*")

# Lấy token bảo mật từ Streamlit Secrets
hf_token = st.secrets.get("HF_TOKEN")

# Khởi tạo mô hình nền tảng cấu hình ngầm
MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"
try:
    client = InferenceClient(model=MODEL_ID, token=hf_token)
except Exception as e:
    st.error(f"Lỗi khởi tạo mô hình: {str(e)}")

# Khởi tạo lịch sử trò chuyện kèm System Prompt định hướng nhân dạng
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system", 
            "content": (
                "Bạn là DeepZero, một hệ thống trợ lý ảo thông minh do dự án DeepZero xây dựng và phát triển "
                "trên nền tảng công nghệ mã nguồn mở. Hãy luôn tự nhận là DeepZero khi giao tiếp với người dùng, "
                "đồng thời cởi mở và minh bạch rằng hệ thống vận dụng các mô hình mã nguồn mở tiên tiến."
            )
        }
    ]

# Hiển thị giao diện lịch sử chat (loại bỏ System Prompt ngầm)
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Hàm ghi nhận dữ liệu phục vụ tự tối ưu & tự học (Self-Learning logs)
def log_for_self_improvement(user_prompt, ai_response):
    log_entry = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] User: {user_prompt} | DeepZero: {ai_response}\n"
    try:
        with open("deepzero_learning_logs.txt", "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception:
        pass

# Xử lý nhập liệu từ người dùng
if prompt := st.chat_input("Nhập câu hỏi hoặc yêu cầu của bạn..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("DeepZero đang xử lý..."):
            try:
                response = client.chat_completion(
                    messages=st.session_state.messages,
                    max_tokens=600,
                    temperature=0.7
                )
                answer = response.choices[0].message.content.strip()
            except Exception as e:
                answer = f"Đã xảy ra lỗi kết nối hệ thống: {str(e)}"
            
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            
            # Lưu log tự học để làm dữ liệu phát triển sau này
            log_for_self_improvement(prompt, answer)
