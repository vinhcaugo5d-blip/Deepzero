from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig, pipeline

app = FastAPI(title="DeepZero AI Worker Node")

print("🔥 Đang khởi động AI Worker...")

model_id = "Qwen/Qwen2.5-7B-Instruct"

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_quant_type="nf4"
)

tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=quantization_config,
    device_map="auto"
)

generator = pipeline("text-generation", model=model, tokenizer=tokenizer)
print("🚀 AI Worker đã sẵn sàng nhận request!")

class AIRequest(BaseModel):
    prompt: str
    max_tokens: int = 300

@app.post("/generate")
def generate_text(req: AIRequest, authorization: str = Header(None)):
    # Có thể thêm lớp bảo mật kiểm tra token từ auth_server ở đây nếu cần
    
    messages = [{"role": "user", "content": req.prompt}]
    text_input = tokenizer.apply_chat_template(
        messages, 
        tokenize=False, 
        add_generation_prompt=True
    )
    
    outputs = generator(
        text_input, 
        max_new_tokens=req.max_tokens, 
        do_sample=True, 
        temperature=0.7,
        top_p=0.9
    )
    
    full_text = outputs[0]['generated_text']
    response_only = full_text.split("<|im_start|>assistant\n")[-1]
    
    return {
        "status": "success",
        "prompt": req.prompt,
        "response": response_only.strip()
    }
