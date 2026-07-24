from datetime import datetime
import os
import random
import time
import google.generativeai as genai
from huggingface_hub import InferenceClient
import streamlit as st

# Cấu hình giao diện trang web
st.set_page_config(
    page_title="DeepZero AI Assistant",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="auto",
)

st.title("🤖 DeepZero AI Assistant (Clean Display Core)")
st.markdown(
    "*Hệ thống trợ lý ảo phát triển bởi DeepZero dựa trên việc ưu tiên sử dụng"
    " các mô hình ngôn ngữ mã nguồn mở hiệu năng cao.*"
)

# Lấy danh sách token từ Streamlit Secrets
hf_tokens = st.secrets.get("HF_TOKENS", [])
if not hf_tokens and "HF_TOKEN" in st.secrets:
  hf_tokens = [st.secrets.get("HF_TOKEN")]

gemini_keys = st.secrets.get("GEMINI_API_KEYS", [])
if not gemini_keys and "GEMINI_API_KEY" in st.secrets:
  gemini_keys = [st.secrets.get("GEMINI_API_KEY")]


# Hàm gọi thông minh có cơ chế thử lại khi lỗi mạng / SSL
def smart_generate_response(formatted_messages, system_instruction):
  last_error = None

  # 1. ƯU TIÊN SỐ 1: Hugging Face Tokens (có thử lại khi rớt mạng)
  if hf_tokens:
    available_hf_tokens = list(hf_tokens)
    random.shuffle(available_hf_tokens)
    hf_models = [
        "Qwen/Qwen2.5-Coder-32B-Instruct",
        "meta-llama/Llama-3.1-8B-Instruct",
        "Qwen/Qwen2.5-7B-Instruct",
    ]

    for token in available_hf_tokens:
      for model_id in hf_models:
        for attempt in range(2):
          try:
            hf_client = InferenceClient(model=model_id, token=token)
            stream = hf_client.chat_completion(
                messages=formatted_messages,
                max_tokens=2048,
                temperature=0.6,
                stream=False,
            )
            if stream.choices and stream.choices[0].message.content:
              return stream.choices[0].message.content
          except Exception as e:
            last_error = e
            time.sleep(1)
            continue

  # 2. DỰ PHÒNG: Google Gemini keys
  if gemini_keys:
    available_gemini_keys = list(gemini_keys)
    random.shuffle(available_gemini_keys)

    for token in available_gemini_keys:
      for attempt in range(2):
        try:
          genai.configure(api_key=token)
          generation_config = {
              "temperature": 0.7,
              "max_output_tokens": 2048,
          }
          model = genai.GenerativeModel(
              model_name="gemini-1.5-flash",
              system_instruction=system_instruction,
              generation_config=generation_config,
          )

          chat_history = []
          for i in range(len(formatted_messages) - 1):
            m = formatted_messages[i]
            role = "user" if m["role"] == "user" else "model"
            chat_history.append({"role": role, "parts": [m["content"]]})

          chat = model.start_chat(history=chat_history)
          last_user_message = formatted_messages[-1]["content"]

          response = chat.send_message(last_user_message)
          if response and response.text:
            return response.text
        except Exception as e:
          last_error = e
          time.sleep(1)
          continue

  raise Exception(
      f"Kết nối mạng tới máy chủ AI bị gián đoạn hoặc hết hạn mức. Chi tiết:"
      f" {str(last_error)}"
  )


# Khởi tạo lịch sử trò chuyện
if "messages" not in st.session_state:
  st.session_state.messages = []

# Cập nhật System Instruction chuẩn hóa hiển thị, không dùng LaTeX thô
system_inch = (
    "Bạn là DeepZero, một hệ thống trợ lý ảo thông minh siêu việt do dự án"
    " DeepZero xây dựng và phát triển. Hệ thống vận hành bằng cách kế thừa, tích"
    " hợp và tối ưu hóa các nền tảng công nghệ mã nguồn mở (open-source) hàng"
    " đầu. Tuyệt đối không dịch sai từ 'open-source' thành tên riêng như Owen,"
    " và không bịa đặt bất kỳ thông tin sai lệch nào. **QUAN TRỌNG:** Khi trình"
    " bày các công thức toán học, tuyệt đối KHÔNG sử dụng các ký hiệu LaTeX phức"
    " tạp hay đóng khung bằng dấu ngoặc vuông như \\[ \\], hãy viết rõ ràng, mạch"
    " lạc bằng văn bản thông thường hoặc ký hiệu ký tự cơ bản (ví dụ: C(5,2)"
    " = (5*4)/(2*1) = 10) để hiển thị không bao giờ bị lỗi trên giao diện"
    " web. Phản hồi của bạn cần sắc sảo, logic và trình bày rõ ràng."
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
      formatted_messages = []
      recent_messages = st.session_state.messages[-15:]
      for m in recent_messages:
        role = "user" if m["role"] == "user" else "assistant"
        formatted_messages.append({"role": role, "content": m["content"]})

      with st.spinner("DeepZero đang phân tích và xử lý yêu cầu..."):
        answer = smart_generate_response(formatted_messages, system_inch)

      st.markdown(answer)
      st.session_state.messages.append(
          {"role": "assistant", "content": answer}
      )
      log_for_self_improvement(prompt, answer)

    except Exception as e:
      error_msg = f"⚠️ Lỗi hệ thống: {str(e)}"
      st.error(error_msg)
      st.session_state.messages.append(
          {"role": "assistant", "content": error_msg}
      )
