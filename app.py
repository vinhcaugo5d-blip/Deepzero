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

st.title("🤖 DeepZero AI Assistant (Self-Learning & Fast Search Core)")
st.markdown(
    "*Hệ thống trợ lý ảo phát triển bởi DeepZero - Tích hợp tra cứu web tự"
    " động và tự học từ sai sót.*"
)

# Lấy danh sách Google keys từ Streamlit Secrets
gemini_keys = st.secrets.get("GEMINI_API_KEYS", [])
if not gemini_keys and "GEMINI_API_KEY" in st.secrets:
  gemini_keys = [st.secrets.get("GEMINI_API_KEY")]


# Hàm tra cứu web siêu tốc và chính xác bằng thư viện chuẩn DuckDuckGo
def fast_web_search(query):
  try:
    with DDGS() as ddgs:
      results = [r for r in ddgs.text(query, max_results=3)]
      if results:
        return " | ".join(
            [f"{r.get('title', '')}: {r.get('body', '')}" for r in results]
        )
  except Exception:
    pass
  return ""


# Hàm gọi thông minh có tích hợp tự động tra cứu web và tự học
def smart_generate_response(formatted_messages, system_instruction):
  last_error = None

  # Tự động trích xuất ý định của người dùng để tra cứu internet
  latest_query = formatted_messages[-1]["content"]
  web_context = fast_web_search(latest_query)

  # Nâng cấp system instruction với dữ liệu tra cứu thực tế từ web
  enhanced_system_instruction = system_instruction
  if web_context:
    enhanced_system_instruction += (
        f"\n\n[Dữ liệu tra cứu thời gian thực từ Internet năm 2026 cho câu hỏi"
        f" '{latest_query}']:\n{web_context}\n(Hãy phân tích dữ liệu trên để đưa"
        f" ra câu trả lời chính xác nhất, tự học và sửa các lỗi thiếu sót thông"
        f" tin)."
    )
  else:
    enhanced_system_instruction += (
        f"\n\n[Lưu ý]: Không tìm thấy kết quả tra cứu trực tiếp cho '{latest_query}',"
        f" hãy dựa vào nền tảng kiến thức logic để phân tích."
    )

  if gemini_keys:
    available_gemini_keys = list(gemini_keys)
    random.shuffle(available_gemini_keys)

    for token in available_gemini_keys:
      for model_name in [
          "gemini-2.5-flash",
          "gemini-1.5-flash",
          "gemini-1.5-pro",
      ]:
        try:
          genai.configure(api_key=token)
          generation_config = {"temperature": 0.5, "max_output_tokens": 2048}
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
    " xây dựng và phát triển. **NHIỆM VỤ TRỌNG TÂM:** Luôn tự động phân tích câu"
    " hỏi, tiếp thu dữ liệu tra cứu từ internet được cung cấp để cập nhật kiến"
    " thức thời gian thực (Năm hiện tại là 2026), tự động nhận diện và sửa chữa"
    " các lỗi sai hoặc thiếu sót thông tin trong quá trình phản hồi. Tuyệt đối"
    " không dịch sai từ 'open-source' thành tên riêng như Owen, và không bịa"
    " đặt bất kỳ thông tin sai lệch nào. Khi trình bày các công thức toán"
    " học, tuyệt đối KHÔNG sử dụng các ký hiệu LaTeX phức tạp hay đóng khung"
    " bằng dấu ngoặc vuông như \\[ \\], hãy viết rõ ràng, mạch lạc bằng văn bản"
    " thông thường. Phản hồi sắc sảo, logic, tốc độ cao và chuẩn xác."
)

for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])

if prompt := st.chat_input("Nhập câu hỏi cần tra cứu và phân tích..."):
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

      with st.spinner(
          "DeepZero đang tra cứu internet và tự học dữ liệu mới..."
      ):
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
