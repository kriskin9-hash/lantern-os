import sys, torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
base_id = sys.argv[1]; adapter = sys.argv[2]; out = sys.argv[3]
print(f"merge: base={base_id} adapter={adapter} -> {out}")
tok = AutoTokenizer.from_pretrained(adapter, trust_remote_code=True)
base = AutoModelForCausalLM.from_pretrained(base_id, torch_dtype=torch.float16, trust_remote_code=True, device_map="cpu")
m = PeftModel.from_pretrained(base, adapter)
m = m.merge_and_unload()
m.save_pretrained(out, safe_serialization=True)
tok.save_pretrained(out)
print("merged OK ->", out)
