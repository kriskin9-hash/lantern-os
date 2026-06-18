#!/usr/bin/env python3
"""
Windows-friendly QLoRA trainer (peft + bitsandbytes + trl) — fallback for when
unsloth won't install (native Windows / no triton).

Trains a LoRA adapter on alpaca {instruction,input,output} data, saves the
adapter, merges to fp16, and writes an Ollama Modelfile. 8 GB VRAM: prefer a
3B base; 7B QLoRA is borderline and may OOM.

Usage:
    .venv-train/Scripts/python scripts/train-qlora-peft.py \
        --base Qwen/Qwen2.5-Coder-3B-Instruct \
        --data models/lantern-sigma0-coder/training-data.jsonl \
        --out  models/lantern-sigma0-coder/adapters \
        --epochs 3
"""
import argparse, json, os


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--base", default="Qwen/Qwen2.5-Coder-3B-Instruct")
    p.add_argument("--data", default="models/lantern-sigma0-coder/training-data.jsonl")
    p.add_argument("--out", default="models/lantern-sigma0-coder/adapters")
    p.add_argument("--epochs", type=int, default=3)
    p.add_argument("--lr", type=float, default=2e-4)
    p.add_argument("--seq", type=int, default=1024)
    p.add_argument("--merge", action="store_true", help="merge adapter to fp16 after training")
    return p.parse_args()


def main():
    a = parse_args()
    import torch
    from datasets import Dataset
    from transformers import (AutoModelForCausalLM, AutoTokenizer,
                              BitsAndBytesConfig, TrainingArguments)
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from trl import SFTTrainer

    print(f"CUDA available: {torch.cuda.is_available()} | base: {a.base}")
    if not torch.cuda.is_available():
        print("ERROR: CUDA not available — aborting (CPU QLoRA is impractical).")
        return 1

    tok = AutoTokenizer.from_pretrained(a.base, trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    bnb = BitsAndBytesConfig(
        load_in_4bit=True, bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        a.base, quantization_config=bnb, device_map="auto", trust_remote_code=True)
    model = prepare_model_for_kbit_training(model)
    model = get_peft_model(model, LoraConfig(
        r=16, lora_alpha=32, lora_dropout=0.05, bias="none", task_type="CAUSAL_LM",
        target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"]))
    model.print_trainable_parameters()

    rows = []
    with open(a.data, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            instr, out = r.get("instruction", ""), r.get("output", "")
            if not instr or not out:
                continue
            rows.append({"text": f"### Instruction:\n{instr}\n\n### Response:\n{out}{tok.eos_token}"})
    print(f"Loaded {len(rows)} training rows")
    ds = Dataset.from_list(rows)

    os.makedirs(a.out, exist_ok=True)
    trainer = SFTTrainer(
        model=model, train_dataset=ds, dataset_text_field="text", max_seq_length=a.seq,
        tokenizer=tok,
        args=TrainingArguments(
            output_dir=a.out, num_train_epochs=a.epochs, per_device_train_batch_size=1,
            gradient_accumulation_steps=8, learning_rate=a.lr, fp16=True,
            logging_steps=5, save_strategy="epoch", optim="paged_adamw_8bit",
            gradient_checkpointing=True, report_to="none"))
    trainer.train()

    final = os.path.join(a.out, "final")
    model.save_pretrained(final); tok.save_pretrained(final)
    print(f"Adapter saved -> {final}")

    if a.merge:
        from peft import AutoPeftModelForCausalLM
        merged = AutoPeftModelForCausalLM.from_pretrained(final, torch_dtype=torch.float16, device_map="auto")
        merged = merged.merge_and_unload()
        mpath = os.path.join(a.out, "merged")
        merged.save_pretrained(mpath); tok.save_pretrained(mpath)
        print(f"Merged fp16 -> {mpath}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
