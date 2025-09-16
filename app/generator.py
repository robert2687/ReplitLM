import os
import asyncio
from typing import Optional

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

from .config import load_config
from .postprocess import clean_code_markers


class CodeGenerator:
    def __init__(self, model_path: str):
        # Lazy load for faster app startup; model loads on first call
        self.model_path = model_path
        self._tokenizer: Optional[AutoTokenizer] = None
        self._model: Optional[AutoModelForCausalLM] = None
        self._cfg = load_config()

    def _ensure_loaded(self):
        if self._tokenizer is not None and self._model is not None:
            return

        # Prefer env-configured paths, then provided model_path, then HF hub
        candidate_paths = [self._cfg.model_local_dir, self.model_path, self._cfg.model_id]
        last_err = None
        for path in candidate_paths:
            try:
                self._tokenizer = AutoTokenizer.from_pretrained(path, trust_remote_code=self._cfg.trust_remote_code)
                use_fp16 = torch.cuda.is_available() and self._cfg.use_fp16_if_available
                dtype = torch.float16 if use_fp16 else None
                self._model = AutoModelForCausalLM.from_pretrained(
                    path,
                    trust_remote_code=self._cfg.trust_remote_code,
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
        # If all attempts failed, re-raise the last error
        if last_err:
            raise last_err

    async def generate_code(self, prompt: str, framework: str = "streamlit", max_new_tokens: Optional[int] = None) -> str:
        # Friendly system prompt to bias toward runnable apps
        system = (
            "You are an AI that writes small, runnable Python apps. "
            "Prefer Streamlit if applicable. Output only code, no explanations."
        )
        wrapped = f"""{system}

Task: Build a minimal {framework} app for the following request:
""" + prompt

        gen_cfg = self._cfg
        max_new = max_new_tokens or gen_cfg.max_new_tokens

        def _run():
            self._ensure_loaded()
            inputs = self._tokenizer(wrapped, return_tensors="pt", truncation=True, max_length=gen_cfg.max_input_tokens)
            if torch.cuda.is_available():
                inputs = {k: v.to("cuda") for k, v in inputs.items()}
            out = self._model.generate(
                **inputs,
                max_new_tokens=max_new,
                do_sample=True,
                temperature=gen_cfg.temperature,
                top_p=gen_cfg.top_p,
                top_k=gen_cfg.top_k,
                eos_token_id=self._tokenizer.eos_token_id,
            )
            text = self._tokenizer.decode(out[0], skip_special_tokens=True, clean_up_tokenization_spaces=False)
            # Return only the completion portion after the prompt
            completion = text.split(prompt, 1)[-1].strip()
            return clean_code_markers(completion)

        return await asyncio.to_thread(_run)