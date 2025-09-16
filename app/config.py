import os
from dataclasses import dataclass


def _get_env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except Exception:
        return default


def _get_env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except Exception:
        return default


def _get_env_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "t", "yes", "y", "on"}


def _get_env_str(name: str, default: str) -> str:
    val = os.getenv(name)
    return val if val is not None else default


@dataclass
class GenerationConfig:
    # Decoding
    max_new_tokens: int = 512
    temperature: float = 0.2
    top_p: float = 0.95
    top_k: int = 50
    # Prompt/tokenization
    max_input_tokens: int = 1024
    # Model loading
    use_fp16_if_available: bool = True
    model_local_dir: str = "replit-code-v1-3b"
    model_id: str = "replit/replit-code-v1-3b"
    trust_remote_code: bool = True


def load_config() -> GenerationConfig:
    return GenerationConfig(
        max_new_tokens=_get_env_int("GEN_MAX_NEW_TOKENS", 512),
        temperature=_get_env_float("GEN_TEMPERATURE", 0.2),
        top_p=_get_env_float("GEN_TOP_P", 0.95),
        top_k=_get_env_int("GEN_TOP_K", 50),
        max_input_tokens=_get_env_int("GEN_MAX_INPUT_TOKENS", 1024),
        use_fp16_if_available=_get_env_bool("USE_FP16", True),
        model_local_dir=_get_env_str("MODEL_LOCAL_DIR", "replit-code-v1-3b"),
        model_id=_get_env_str("MODEL_ID", "replit/replit-code-v1-3b"),
        trust_remote_code=_get_env_bool("TRUST_REMOTE_CODE", True),
    )