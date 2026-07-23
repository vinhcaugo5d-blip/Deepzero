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

# Giao diện tiêu đề chính
st.title("🤖 DeepZero AI Assistant (Online 24/7)")
st.markdown(
    "*Hệ thống trợ lý ảo phát triển bởi DeepZero dựa trên việc kế thừa và tối"
    " ưu hóa các nền tảng công nghệ mã nguồn mở.*"
)

# Lấy danh sách API keys từ Streamlit Secrets an toàn tuyệt đối
api_keys = st.secrets.get("GEMINI_API_KEYS", [])

# Fallback nếu dùng cấu hình đơn lẻ
if not api_keys and "GEMINI_API_KEY" in st.secrets:
  api_keys = [st.secrets.get("GEMINI_API_KEY")]


# Hàm cấu hình và khởi tạo mô hình Gemini với cơ chế xoay vòng thông minh
def get_random_gemini_model():
  if not api_keys:
    raise ValueError(
        "Chưa cấu hình danh sách GEMINI_API_KEYS trong Streamlit Secrets!"
    )

  chosen_key = random.choice(api_keys)
  genai.configure(api_key=chosen_key)
  generation_config = {"temperature": 0.7, "max_output_tokens": 600}
  # Sử dụng gemini-2.5-flash chuẩn ổn định cho production
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

# Định nghĩa System Instructions nhận diện thương hiệu DeepZero
system_instruction_content = (
    "Bạn là DeepZero, một hệ thống trợ lý ảo thông minh do dự án DeepZero xây"
    " dựng và phát triển. Hệ thống vận hành bằng cách kế thừa, tích hợp và"
    " tối ưu hóa các nền tảng công nghệ mã nguồn mở (open-source) hàng đầu."
    " Tuyệt đối không dịch sai từ 'open-source' thành tên riêng như Owen, và"
    " không bịa đặt bất kỳ thông tin sai lệch nào. Luôn giữ thái độ trung thực,"
    " minh bạch rằng DeepZero sử dụng mã nguồn mở làm nền tảng để tinh chỉnh và"
    " phát triển."
)

# Hiển thị giao diện lịch sử chat
for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])


# Hàm ghi nhận dữ liệu phục vụ tự tối ưu & tự học (Self-Learning logs)
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


# Xử lý nhập liệu từ người dùng
if prompt := st.chat_input("Nhập câu hỏi hoặc yêu cầu của bạn..."):
  st.session_state.messages.append({"role": "user", "content": prompt})
  with st.chat_message("user"):
    st.markdown(prompt)

  with st.chat_message("assistant"):
    with st.spinner("DeepZero đang xử lý..."):
      try:
        active_model = get_random_gemini_model()

        chat_history = []
        for m in st.session_state.messages[:-1]:
          role_mapped = "user" if m["role"] == "user" else "model"
          chat_history.append({"role": role_mapped, "parts": [m["content"]]})

        chat_session = active_model.start_chat(history=chat_history)
        response = chat_session.send_message(
            f"[System Directive]: {system_instruction_content}\n\nUser request:"
            f" {prompt}"
        )

        answer = response.text.strip()
      except Exception as e:
        answer = f"Đã xảy ra lỗi kết nối hệ thống: {str(e)}"

      st.markdown(answer)
      st.session_state.messages.append({"role": "assistant", "content": answer})

      log_for_self_improvement(prompt, answer)
