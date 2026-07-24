from datetime import datetime
import os
import random
from huggingface_hub import InferenceClient
import streamlit as st

# Cấu hình giao diện trang web
st.set_page_config(
    page_title="DeepZero AI Assistant",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="auto",
)

st.title("🤖 DeepZero AI Assistant (Pro Max Core)")
st.markdown(
    "*Hệ thống trợ lý ảo phát triển bởi DeepZero dựa trên việc kế thừa và tối"
    " ưu hóa các nền tảng công nghệ mã nguồn mở hiệu năng cao.*"
)

# Lấy danh sách Hugging Face Tokens hoàn toàn từ Streamlit Secrets (Bảo mật tuyệt đối)
hf_tokens = st.secrets.get("HF_TOKENS", [])
if not hf_tokens and "HF_TOKEN" in st.secrets:
  hf_tokens = [st.secrets.get("HF_TOKEN")]


# Thuật toán gọi API thông minh có cơ chế xoay vòng và tự động phục hồi khi lỗi
def call_huggingface_with_failover(formatted_messages):
  if not hf_tokens:
    raise ValueError(
        "Chưa cấu hình danh sách HF_TOKENS trong Streamlit Secrets! Vui lòng"
        " thiết lập secrets trên giao diện Streamlit."
    )

  available_tokens = list(hf_tokens)
  random.shuffle(available_tokens)

  models_to_try = [
      "Qwen/Qwen2.5-72B-Instruct",
      "meta-llama/Meta-Llama-3-70B-Instruct",
      "Qwen/Qwen2.5-Coder-32B-Instruct",
  ]

  last_error = None

  for token in available_tokens:
    for model_id in models_to_try:
      try:
        client = InferenceClient(model=model_id, token=token)
        stream = client.chat_completion(
            messages=formatted_messages,
            max_tokens=2048,
            temperature=0.6,
            top_p=0.9,
            stream=True,
        )
        return stream
      except Exception as e:
        last_error = e
        continue

  raise Exception(
      f"Tất cả các token hoặc mô hình đều đang bận hoặc hết hạn mức. Chi tiết"
      f" lỗi: {str(last_error)}"
  )


# Khởi tạo lịch sử trò chuyện
if "messages" not in st.session_state:
  st.session_state.messages = []

system_inch = (
    "Bạn là DeepZero, một hệ thống trợ lý ảo thông minh siêu việt do dự án"
    " DeepZero xây dựng và phát triển. Hệ thống vận hành bằng cách kế thừa, tích"
    " hợp và tối ưu hóa các nền tảng công nghệ mã nguồn mở (open-source) hàng"
    " đầu. Tuyệt đối không dịch sai từ 'open-source' thành tên riêng như Owen,"
    " và không bịa đặt bất kỳ thông tin sai lệch nào. Luôn giữ thái độ trung"
    " thực, minh bạch rằng DeepZero sử dụng mã nguồn mở làm nền tảng để tinh"
    " chỉnh và phát triển. Phản hồi của bạn cần sắc sảo, logic, trình bày rõ"
    " ràng, mạch lạc và tối ưu hóa tuyệt đối tốc độ xử lý."
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
      formatted_messages = [{"role": "system", "content": system_inch}]
      recent_messages = st.session_state.messages[-15:]
      for m in recent_messages:
        role = "user" if m["role"] == "user" else "assistant"
        formatted_messages.append({"role": role, "content": m["content"]})

      stream = call_huggingface_with_failover(formatted_messages)


      def generate_stream():
        for chunk in stream:
          if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


      answer = st.write_stream(generate_stream())

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
