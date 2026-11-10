"""Central Ollama wrapper: chat, structured output, embeddings, tool calling."""
import ollama
from typing import Type, TypeVar, Any
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

MODELS = {
    "fast":    "qwen2.5:1.5b",
    "default": "qwen2.5:3b",
    "deep":    "qwen2.5:3b",
    "max":     "qwen2.5:3b",
}
DEFAULT_MODEL = MODELS["default"]
PARSER_MODEL = MODELS["fast"]
EMBED_MODEL = "nomic-embed-text"
EMBED_DIM = 768

def chat_text(prompt: str, system: str = "", model: str = DEFAULT_MODEL, temperature: float = 0.0) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    resp = ollama.chat(
        model=model,
        messages=messages,
        options={"temperature": temperature, "num_ctx": 8192},
    )
    return resp["message"]["content"]

def chat_structured(prompt: str, schema: Type[T], system: str = "", model: str = DEFAULT_MODEL) -> T:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    resp = ollama.chat(
        model=model,
        messages=messages,
        format=schema.model_json_schema(),
        options={"temperature": 0.0, "num_ctx": 8192},
    )
    return schema.model_validate_json(resp["message"]["content"])

def chat_with_tools(prompt: str, tools: list, messages: list | None = None, model: str = DEFAULT_MODEL) -> Any:
    msgs = messages or []
    if not msgs:
        msgs.append({"role": "user", "content": prompt})
    return ollama.chat(model=model, messages=msgs, tools=tools, options={"num_ctx": 8192})

def embed(text: str, model: str = EMBED_MODEL) -> list[float]:
    """Return a 768-dim embedding. Never raises — returns zero vector on failure."""
    text = (text or "").strip()
    if not text:
        return [0.0] * EMBED_DIM
    text = text[:6000]
    try:
        resp = ollama.embed(model=model, input=text)
        vecs = resp.get("embeddings") or []
        if vecs and vecs[0]:
            return list(vecs[0])
    except Exception:
        pass
    return [0.0] * EMBED_DIM

def embed_batch(texts: list[str], model: str = EMBED_MODEL) -> list[list[float]]:
    if not texts:
        return []
    cleaned = [(t or "").strip()[:6000] or " " for t in texts]
    try:
        resp = ollama.embed(model=model, input=cleaned)
        vecs = resp.get("embeddings") or []
        if len(vecs) == len(cleaned):
            return [list(v) if v else [0.0] * EMBED_DIM for v in vecs]
    except Exception:
        pass
    return [[0.0] * EMBED_DIM for _ in cleaned]

def cosine_sim(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0