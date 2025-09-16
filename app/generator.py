import os
import asyncio
from typing import Optional

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM


class CodeGenerator:
    def __init__(self, model_path: str):
        # Lazy load for faster app startup; model loads on first call
        self.model_path = model_path
        self._tokenizer: Optional[AutoTokenizer] = None
        self._model: Optional[AutoModelForCausalLM] = None

    def _ensure_loaded(self):
        if self._tokenizer is not None and self._model is not None:
            return

        # Try local path first, fall back to HF hub if weights aren't present
        candidate_paths = [self.model_path, "replit/replit-code-v1-3b"]
        last_err = None
        for path in candidate_paths:
            try:
                self._tokenizer = AutoTokenizer.from_pretrained(path, trust_remote_code=True)
                dtype = torch.float16 if torch.cuda.is_available() else None
                self._model = AutoModelForCausalLM.from_pretrained(
                    path,
                    trust_remote_code=True,
                    torch_dtype=dtype,
                )
                if torch.cuda.is_available():
                    self._model = self._model.to("cuda")
                self._model.eval()
                return
            except Exception as e:
                last_err = e
                self._tokenizer = None
                self._model = None
                continue
        # If both attempts failed, re-raise the last error
        if last_err:
            raise last_err

    async def generate_code(self, prompt: str, framework: str = "streamlit", max_new_tokens: int = 512) -> str:
        # Friendly system prompt to bias toward runnable apps
        system = (
            "You are an AI that writes small, runnable Python apps. "
            "Prefer Streamlit if applicable. Output only code, no explanations."
        )
        wrapped = f"""{system}

Task: Build a minimal {framework} app for the following request:
""" + prompt

        def _run():
            self._ensure_loaded()
            inputs = self._tokenizer(wrapped, return_tensors="pt")
            if torch.cuda.is_available():
                inputs = {k: v.to("cuda") for k, v in inputs.items()}
            out = self._model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=True,
                temperature=0.2,
                top_p=0.95,
                eos_token_id=self._tokenizer.eos_token_id,
            )
            text = self._tokenizer.decode(out[0], skip_special_tokens=True, clean_up_tokenization_spaces=False)
            # Return only the completion portion after the prompt
            return text.split(prompt, 1)[-1].strip()

        return await asyncio.to_thread(_run)