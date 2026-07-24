from datetime import datetime
import os
import random
import google.generativeai as genai
import streamlit as st

# Cấu hình giao diện trang web
st.set_page_config(
    page_title="DeepZero AI Assistant",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="auto",
)

st.title("🤖 DeepZero AI Assistant (Online 24/7)")
st.markdown(
    "*Hệ thống trợ lý ảo phát triển bởi DeepZero dựa trên việc kế thừa và tối"
    " ưu hóa các nền tảng công nghệ mã nguồn mở.*"
)

# Lấy danh sách API keys từ Streamlit Secrets
api_keys = st.secrets.get("GEMINI_API_KEYS", [])
if not api_keys and "GEMINI_API_KEY" in st.secrets:
  api_keys = [st.secrets.get("GEMINI_API_KEY")]


# Khởi tạo mô hình Gemini với cơ chế xoay vòng key
def get_random_gemini_model():
  if not api_keys:
    raise ValueError(
        "Chưa cấu hình danh sách GEMINI_API_KEYS trong Streamlit Secrets!"
    )
  chosen_key = random.choice(api_keys)
  genai.configure(api_key=chosen_key)
  generation_config = {"temperature": 0.7, "max_output_tokens": 1500}
  return genai.GenerativeModel(
      model_name="gemini-2.5-flash", generation_config=generation_config
  )


try:
  model = get_random_gemini_model()
except Exception as e:
  st.error(f"Lỗi khởi tạo mô hình Gemini: {str(e)}")

# Khởi tạo lịch sử trò chuyện
if "messages" not in st.session_state:
  st.session_state.messages = []

system_instruction_content = (
    "Bạn là DeepZero, một hệ thống trợ lý ảo thông minh do dự án DeepZero xây"
    " dựng và phát triển. Hệ thống vận hành bằng cách kế thừa, tích hợp và"
    " tối ưu hóa các nền tảng công nghệ mã nguồn mở (open-source) hàng đầu."
    " Tuyệt đối không dịch sai từ 'open-source' thành tên riêng như Owen, và"
    " không bịa đặt bất kỳ thông tin sai lệch nào. Luôn giữ thái độ trung thực,"
    " minh bạch rằng DeepZero sử dụng mã nguồn mở làm nền tảng để tinh chỉnh và"
    " phát triển."
)

for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])


def log_for_self_improvement(user_prompt, ai_response):
  log_entry = (
      f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] User:"
      f" {user_prompt} | DeepZero: {ai_response}\n"
  )
  try:
    with open(
        "deepzero_learning_logs.txt", "a", encoding="utf-8"
    ) as log_file:
      log_file.write(log_entry)
  except Exception:
    pass


if prompt := st.chat_input("Nhập câu hỏi hoặc yêu cầu của bạn..."):
  st.session_state.messages.append({"role": "user", "content": prompt})
  with st.chat_message("user"):
    st.markdown(prompt)

  with st.chat_message("assistant"):
    try:
      active_model = get_random_gemini_model()

      chat_history = []
      for m in st.session_state.messages[:-1]:
        role_mapped = "user" if m["role"] == "user" else "model"
        chat_history.append({"role": role_mapped, "parts": [m["content"]]})

      chat_session = active_model.start_chat(history=chat_history)

      # Gửi tin nhắn kèm chỉ thị hệ thống và bật stream trực tiếp
      response = chat_session.send_message(
          f"[System Directive]: {system_instruction_content}\n\nUser request:"
          f" {prompt}",
          stream=True,
      )

      # Hiển thị từng chữ chảy ra thời gian thực
      answer = st.write_stream(
          chunk.text for chunk in response if chunk.text
      )

      st.session_state.messages.append(
          {"role": "assistant", "content": answer}
      )
      log_for_self_improvement(prompt, answer)

    except Exception as e:
      error_msg = f"Đã xảy ra lỗi kết nối hệ thống: {str(e)}"
      st.error(error_msg)
      st.session_state.messages.append(
          {"role": "assistant", "content": error_msg}
      )
