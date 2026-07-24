from datetime import datetime
import os
import random
import requests
import streamlit as st

# Cấu hình giao diện trang web
st.set_page_config(
    page_title="DeepZero AI Assistant",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="auto",
)

st.title("🤖 DeepZero AI Assistant (Stable Core)")
st.markdown(
    "*Hệ thống trợ lý ảo phát triển bởi DeepZero - Tối ưu hóa độ ổn định và"
    " chống đóng luồng.*"
)

# Lấy danh sách Hugging Face Tokens từ Streamlit Secrets
hf_tokens = st.secrets.get("HF_TOKENS", [])
if not hf_tokens and "HF_TOKEN" in st.secrets:
  hf_tokens = [st.secrets.get("HF_TOKEN")]

# Dự phòng Google keys
gemini_keys = st.secrets.get("GEMINI_API_KEYS", [])
if not gemini_keys and "GEMINI_API_KEY" in st.secrets:
  gemini_keys = [st.secrets.get("GEMINI_API_KEY")]


# Hàm hỗ trợ tra cứu thông tin nhanh trên web (dùng DuckDuckGo API)
def search_web(query):
  try:
    url = "https://html.duckduckgo.com/html/"
    headers = {"User-Agent": "Mozilla/5.0"}
    data = {"q": query}
    response = requests.post(url, headers=headers, data=data, timeout=4)
    if response.status_code == 200:
      from bs4 import BeautifulSoup

      soup = BeautifulSoup(response.text, "html.parser")
      results = []
      for a in soup.find_all("a", class_="result__snippet", limit=2):
        results.append(a.get_text())
      if results:
        return " | ".join(results)
  except Exception:
    pass
  return ""


# Hàm gọi thông minh chống lỗi đóng luồng tuyệt đối
def smart_generate_response(formatted_messages, system_instruction):
  last_error = None

  latest_query = formatted_messages[-1]["content"]
  web_context = search_web(latest_query)

  enhanced_system_instruction = system_instruction
  if web_context:
    enhanced_system_instruction += (
        f"\n\n[Dữ liệu tra cứu thời gian thực từ Internet năm 2026]:"
        f" {web_context}"
    )

  # 1. Ưu tiên tuyệt đối Hugging Face qua HTTP trực tiếp (Đảm bảo stream=False)
  if hf_tokens:
    available_hf_tokens = list(hf_tokens)
    random.shuffle(available_hf_tokens)

    api_url = (
        "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-7B-Instruct/v1/chat/completions"
    )
    full_messages = [
        {"role": "system", "content": enhanced_system_instruction}
    ] + formatted_messages

    for token in available_hf_tokens:
      headers = {
          "Authorization": f"Bearer {token}",
          "Content-Type": "application/json",
      }
      payload = {
          "model": "Qwen/Qwen2.5-7B-Instruct",
          "messages": full_messages,
          "max_tokens": 1500,
          "temperature": 0.6,
          "stream": False,  # Bắt buộc ép False để chống lỗi đóng luồng
      }

      try:
        response = requests.post(
            api_url, headers=headers, json=payload, timeout=12
        )
        if response.status_code == 200:
          res_json = response.json()
          if "choices" in res_json and len(res_json["choices"]) > 0:
            content = res_json["choices"][0]["message"]["content"]
            if content:
              return content
        else:
          last_error = f"HTTP {response.status_code}: {response.text}"
      except Exception as e:
        last_error = e
        continue

  # 2. Dự phòng bằng Google Gemini nếu HF gặp sự cố
  if gemini_keys:
    import google.generativeai as genai

    available_gemini_keys = list(gemini_keys)
    random.shuffle(available_gemini_keys)
    for token in available_gemini_keys:
      try:
        genai.configure(api_key=token)
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=enhanced_system_instruction,
        )
        chat_history = [
            {
                "role": "user" if m["role"] == "user" else "model",
                "parts": [m["content"]],
            }
            for m in formatted_messages[:-1]
        ]
        chat = model.start_chat(history=chat_history)
        res = chat.send_message(formatted_messages[-1]["content"])
        if res and res.text:
          return res.text
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
    "Bạn là DeepZero, một hệ thống trợ lý ảo thông minh siêu việt do dự án"
    " DeepZero xây dựng và phát triển. **THÔNG TIN QUAN TRỌNG VỀ THỜI GIAN:**"
    " Hiện tại đang là năm 2026. Mọi dữ liệu, thông tin thời sự hay câu hỏi đều"
    " phải căn cứ vào mốc năm 2026. Tuyệt đối không dịch sai từ 'open-source'"
    " thành tên riêng như Owen, và không bịa đặt bất kỳ thông tin sai lệch"
    " nào. Khi trình bày các công thức toán học, tuyệt đối KHÔNG sử dụng các ký"
    " hiệu LaTeX phức tạp hay đóng khung bằng dấu ngoặc vuông như \\[ \\], hãy"
    " viết rõ ràng, mạch lạc bằng văn bản thông thường hoặc ký hiệu ký tự cơ"
    " bản. Phản hồi của bạn cần sắc sảo, logic và trình bày rõ ràng."
)

for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["content"])

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

      with st.spinner("DeepZero đang phân tích và xử lý..."):
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
