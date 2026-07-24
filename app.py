from datetime import datetime
import os
import random
import streamlit as st
from duckduckgo_search import DDGS
from huggingface_hub import InferenceClient

# Cấu hình giao diện trang web
st.set_page_config(
    page_title="DeepZero AI Assistant",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="auto",
)

st.title("🤖 DeepZero AI Assistant (Stable Hub Core)")
st.markdown(
    "*Trợ lý ảo tối ưu hóa tốc độ cao - Kết nối chuẩn qua Hugging Face Hub"
    " Client.*"
)

# Lấy token Hugging Face từ Streamlit Secrets
hf_tokens = st.secrets.get("HF_TOKENS", [])
if not hf_tokens and "HF_TOKEN" in st.secrets:
  hf_tokens = [st.secrets.get("HF_TOKEN")]


# Hàm kiểm tra xem câu hỏi có cần tra cứu internet hay không
def needs_web_search(query):
  query_lower = query.lower()
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


# Hàm tra cứu web nhanh gọn bằng DuckDuckGo
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


# Hàm gọi thông minh sử dụng InferenceClient chuẩn của Hugging Face
def smart_generate_response(formatted_messages, system_instruction):
  last_error = None
  latest_query = formatted_messages[-1]["content"]

  # Chỉ tra cứu web khi câu hỏi yêu cầu dữ liệu thời sự thực tế
  enhanced_system_instruction = system_instruction
  if needs_web_search(latest_query):
    web_context = fast_web_search(latest_query)
    if web_context:
      enhanced_system_instruction += (
          f"\n\n[Dữ liệu tra cứu internet thời gian thực năm 2026 cho"
          f" '{latest_query}']: {web_context}\n(Hãy tự động phân tích kỹ dữ liệu"
          f" này để cập nhật, tự sửa các lỗi thông tin cũ và đưa ra câu trả"
          f" lời chính xác nhất)."
      )

  full_messages = [
      {"role": "system", "content": enhanced_system_instruction}
  ] + formatted_messages

  if hf_tokens:
    available_hf_tokens = list(hf_tokens)
    random.shuffle(available_hf_tokens)

    # Danh sách các model mã nguồn mở hàng đầu hiện tại
    hf_models = [
        "Qwen/Qwen2.5-7B-Instruct",
        "meta-llama/Llama-3.1-8B-Instruct",
    ]

    for token in available_hf_tokens:
      for model_id in hf_models:
        try:
          client = InferenceClient(model=model_id, token=token)
          response = client.chat.completions.create(
              messages=full_messages,
              max_tokens=1500,
              temperature=0.5,
              stream=False,
          )
          if (
              response
              and response.choices
              and response.choices[0].message.content
          ):
            return response.choices[0].message.content
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
    " thật tự nhiên, sắc sảo, tự động kiểm tra và sửa lỗi sai thông tin dựa"
    " trên dữ liệu thực tế. Tuyệt đối không dịch sai từ 'open-source' thành"
    " tên riêng như Owen, và không bịa đặt thông tin. Khi trình bày công thức"
    " toán học, tuyệt đối KHÔNG dùng LaTeX phức tạp hay đóng khung bằng ngoặc"
    " vuông \\[ \\], hãy viết ký hiệu cơ bản rõ ràng."
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

      with st.spinner("DeepZero đang phân tích..."):
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
