from datetime import datetime
import os
import random
import re
import streamlit as st
from duckduckgo_search import DDGS
from huggingface_hub import InferenceClient

st.set_page_config(
    page_title="DeepZero AI Assistant",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="auto",
)

st.title("🤖 DeepZero AI Assistant (Clean Stable Core)")
st.markdown(
    "*Trợ lý ảo tối ưu hóa tốc độ cao - Nền tảng ổn định, tự động tra cứu"
    " thông minh.*"
)

hf_tokens = st.secrets.get("HF_TOKENS", [])
if not hf_tokens and "HF_TOKEN" in st.secrets:
  hf_tokens = [st.secrets.get("HF_TOKEN")]


def web_search(query):
  try:
    with DDGS() as ddgs:
      results = [r for r in ddgs.text(query, max_results=3)]
      if results:
        return " | ".join(
            [f"{r.get('title', '')}: {r.get('body', '')}" for r in results]
        )
  except Exception:
    pass
  return "Không tìm thấy kết quả phù hợp."


def smart_generate_response(formatted_messages, system_instruction):
  last_error = None

  if not hf_tokens:
    raise Exception(
        "Chưa cấu hình Hugging Face Token trong Streamlit Secrets (HF_TOKENS hoặc"
        " HF_TOKEN)."
    )

  available_hf_tokens = list(hf_tokens)
  random.shuffle(available_hf_tokens)

  models_to_try = [
      "Qwen/Qwen2.5-7B-Instruct",
      "meta-llama/Llama-3.1-8B-Instruct",
  ]

  for token in available_hf_tokens:
    for model_id in models_to_try:
      try:
        client = InferenceClient(model=model_id, token=token)

        full_messages = [
            {"role": "system", "content": system_instruction}
        ] + formatted_messages
        response = client.chat.completions.create(
            messages=full_messages,
            max_tokens=1500,
            temperature=0.4,
            stream=False,
        )

        if not response or not response.choices:
          continue

        initial_reply = response.choices[0].message.content

        search_match = re.search(r"\[SEARCH:\s*(.*?)\]", initial_reply)
        if search_match:
          search_query = search_match.group(1).strip()
          search_data = web_search(search_query)

          follow_up_messages = full_messages + [
              {"role": "assistant", "content": initial_reply},
              {
                  "role": "user",
                  "content": (
                      f"[Hệ thống tự động tra cứu thông tin cho từ khóa"
                      f" '{search_query}']: {search_data}\n\nHãy dựa vào dữ"
                      f" liệu thực tế này để viết câu trả lời chính xác, đầy đủ"
                      f" và tự nhiên nhất cho người dùng (tuyệt đối không hiển"
                      f" thị thẻ [SEARCH] nữa)."
                  ),
              },
          ]

          final_response = client.chat.completions.create(
              messages=follow_up_messages,
              max_tokens=1500,
              temperature=0.4,
              stream=False,
          )

          if (
              final_response
              and final_response.choices
              and final_response.choices[0].message.content
          ):
            return final_response.choices[0].message.content

        if initial_reply:
          return initial_reply

      except Exception as e:
        last_error = e
        continue

  raise Exception(
      f"Hệ thống bận hoặc hết hạn mức. Chi tiết lỗi cuối: {str(last_error)}"
  )


if "messages" not in st.session_state:
  st.session_state.messages = []

system_inch = (
    "Bạn là DeepZero, hệ thống trợ lý ảo thông minh siêu việt do dự án DeepZero"
    " xây dựng và phát triển. Mốc thời gian hiện tại là tháng 7 năm 2026. **QUY"
    " TẮC TRA CỨU:** Khi người dùng hỏi về các thông tin thời sự, sự kiện, lịch"
    " chiếu phim/anime (ví dụ Mushoku Tensei mùa 3 tập 8), luật pháp, giá cả"
    " hoặc bất kỳ dữ liệu thực tế nào cần độ chính xác cao, hãy tự động phân"
    " tích và đưa ra cú pháp yêu cầu tra cứu theo định dạng: [SEARCH:"
    " từ_khóa_cần_tìm] ngay trong câu trả lời của bạn. Nếu là câu chào hỏi"
    " hoặc kiến thức cơ bản thông thường, hãy trả lời trực tiếp ngay lập tức."
    " Tuyệt đối không dịch sai từ 'open-source' thành tên riêng như Owen, và"
    " không bịa đặt thông tin. Khi trình bày công thức toán học, tuyệt đối"
    " KHÔNG dùng LaTeX phức tạp hay đóng khung bằng ngoặc vuông \\[ \\], hãy"
    " viết ký hiệu cơ bản rõ ràng."
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
