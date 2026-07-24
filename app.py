from datetime import datetime
import os
import random
import streamlit as st
import google.generativeai as genai
from duckduckgo_search import DDGS

# Cấu hình giao diện trang web
st.set_page_config(
    page_title="DeepZero AI Assistant",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="auto",
)

st.title("🤖 DeepZero AI Assistant (Optimized Core)")
st.markdown(
    "*Trợ lý ảo thông minh tốc độ cao - Tự động tra cứu thông minh khi cần thiết.*"
)

# Lấy danh sách Google keys từ Streamlit Secrets
gemini_keys = st.secrets.get("GEMINI_API_KEYS", [])
if not gemini_keys and "GEMINI_API_KEY" in st.secrets:
  gemini_keys = [st.secrets.get("GEMINI_API_KEY")]


# Hàm kiểm tra xem câu hỏi có thực sự cần tra cứu web hay không
def needs_web_search(query):
  query_lower = query.lower()
  # Các từ khóa kích hoạt tra cứu internet
  keywords = [
      "tin tức",
      "hôm nay",
      "mới nhất",
      "là ai",
      "bao nhiêu",
      "năm 2026",
      "sự kiện",
      "giá",
      "thời tiết",
      "bóng đá",
      "kết quả",
  ]
  return any(kw in query_lower for kw in keywords)


# Hàm tra cứu web nhanh gọn
def fast_web_search(query):
  try:
    with DDGS() as ddgs:
      results = [r for r in ddgs.text(query, max_results=2)]
      if results:
        return " | ".join(
            [f"{r.get('title', '')}: {r.get('body', '')}" for r in results]
        )
  except Exception:
    pass
  return ""


# Hàm gọi thông minh tối ưu tốc độ
def smart_generate_response(formatted_messages, system_instruction):
  last_error = None
  latest_query = formatted_messages[-1]["content"]

  # Chỉ tra cứu web khi thực sự cần thiết để đảm bảo tốc độ phản hồi nhanh nhất
  enhanced_system_instruction = system_instruction
  if needs_web_search(latest_query):
    web_context = fast_web_search(latest_query)
    if web_context:
      enhanced_system_instruction += (
          f"\n\n[Dữ liệu tra cứu internet năm 2026 cho '{latest_query}']: {web_context}"
      )

  if gemini_keys:
    available_gemini_keys = list(gemini_keys)
    random.shuffle(available_gemini_keys)

    for token in available_gemini_keys:
      # Sửa lại danh sách model chuẩn hiện hành, ưu tiên flash tốc độ cao
      for model_name in ["gemini-2.5-flash", "gemini-1.5-flash"]:
        try:
          genai.configure(api_key=token)
          generation_config = {"temperature": 0.6, "max_output_tokens": 2048}
          model = genai.GenerativeModel(
              model_name=model_name,
              system_instruction=enhanced_system_instruction,
              generation_config=generation_config,
          )

          chat_history = []
          for i in range(len(formatted_messages) - 1):
            m = formatted_messages[i]
            role = "user" if m["role"] == "user" else "model"
            chat_history.append({"role": role, "parts": [m["content"]]})

          chat = model.start_chat(history=chat_history)
          response = chat.send_message(latest_query)
          if response and response.text:
            return response.text
        except Exception as e:
          last_error = e
          continue

  raise Exception(
      f"Hệ thống bận hoặc token hết hạn mức. Chi tiết lỗi cuối: {str(last_error)}"
  )


# Khởi tạo lịch sử trò chuyện
if "messages" not in st.session_state:
  st.session_state.messages = []

system_inch = (
    "Bạn là DeepZero, hệ thống trợ lý ảo thông minh siêu việt do dự án DeepZero"
    " xây dựng và phát triển. Mốc thời gian hiện tại là năm 2026. Hãy phản hồi"
    " thật tự nhiên, nhanh chóng, sắc sảo và đúng trọng tâm. Tuyệt đối không"
    " dịch sai từ 'open-source' thành tên riêng như Owen, và không bịa đặt"
    " thông tin. Khi trình bày công thức toán học, tuyệt đối KHÔNG dùng LaTeX"
    " phức tạp hay đóng khung bằng ngoặc vuông \\[ \\], hãy viết ký hiệu cơ"
    " bản rõ ràng."
)

for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])

if prompt := st.chat_input("Nhập câu hỏi của bạn..."):
  st.session_state.messages.append({"role": "user", "content": prompt})
  with st.chat_message("user"):
    st.markdown(prompt)

  with st.chat_message("assistant"):
    try:
      formatted_messages = []
      recent_messages = st.session_state.messages[-15:]
      for m in recent_messages:
        role = "user" if m["role"] == "user" else "assistant"
        formatted_messages.append({"role": role, "content": m["content"]})

      with st.spinner("DeepZero đang trả lời..."):
        answer = smart_generate_response(formatted_messages, system_inch)

      st.markdown(answer)
      st.session_state.messages.append(
          {"role": "assistant", "content": answer}
      )

    except Exception as e:
      error_msg = f"⚠️ Lỗi hệ thống: {str(e)}"
      st.error(error_msg)
      st.session_state.messages.append(
          {"role": "assistant", "content": error_msg}
      )
