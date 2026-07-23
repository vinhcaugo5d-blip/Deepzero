import streamlit as st
import os
from huggingface_hub import InferenceClient

st.set_page_config(page_title="DeepZero AI Assistant", page_icon="🤖", layout="centered")

st.title("🤖 DeepZero AI Assistant (Online 24/7)")
st.write("Hệ thống trợ lý ảo thông minh tích hợp Self-Healing.")

# Lấy token từ Streamlit Secrets để ai cũng dùng được mà không cần nhập token
hf_token = st.secrets.get("HF_TOKEN")

# Khởi tạo Hugging Face Inference Client với mô hình Qwen và token bảo mật
MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"
client = InferenceClient(model=MODEL_ID, token=hf_token)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Nhập câu hỏi của bạn..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("AI đang xử lý..."):
            try:
                # Chuyển đổi lịch sử chat phù hợp với định dạng của client
                messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                response = client.chat_completion(
                    messages=messages,
                    max_tokens=600,
                    temperature=0.7
                )
                answer = response.choices[0].message.content.strip()
            except Exception as e:
                answer = f"Đã xảy ra lỗi kết nối mô hình: {str(e)}"
            
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
