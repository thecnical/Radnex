"""APInex — a unified LLM + tools API gateway, as a Radnex source.

APInex (https://apinex.bond) provides an OpenAI and Anthropic Messages compatible gateway
supporting GPT, Claude, Gemini, Kimi, DeepSeek, GLM and Grok.
It serves the Anthropic Messages protocol at POST /v1/messages natively.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

RADNEX_HOME = Path(
    os.environ.get("RADNEX_HOME")
    or os.environ.get("ZIMZILLA_HOME")
    or (Path.home() / ".radnex")
)
CLAUDE_SOURCE = Path(
    os.environ.get("RADNEX_CLAUDE_SOURCE")
    or os.environ.get("ZIMZILLA_CLAUDE_SOURCE")
    or (Path.home() / "claude-source")
)

HOST = "apinex.bond"
DEFAULT_BASE_URL = "https://api.apinex.bond"
PROFILE = RADNEX_HOME / "apinex" / "source"
CACHE_TTL = 300.0

FREE_SUFFIXES = ("-free", ":free")

PREFERRED_FREE_MODELS = (
    "deepseek-v4.1-flash",
    "gemini-2.5-flash",
    "glm-4.5-flash",
    "qwen-2.5-coder-32b",
)


@dataclass(frozen=True)
class Model:
    """One entry from APInex's catalog."""

    id: str
    label: str = ""
    context_length: int | None = None
    max_output: int | None = None
    price_in: float = 0.0
    price_out: float = 0.0
    types: str = "llm"
    tools: bool = True
    free: bool = False
    reasoning: bool = False
    priced: bool = False

    @property
    def chat(self) -> bool:
        return "llm" in self.types

    @property
    def blurb(self) -> str:
        bits = []
        if self.free:
            bits.append("free")
        elif self.price_in or self.price_out:
            bits.append(f"${self.price_in:g}/${self.price_out:g}")
        if self.context_length:
            bits.append(f"{self.context_length // 1000}k ctx")
        if self.reasoning:
            bits.append("reasoning")
        return " · ".join(bits)


def current_key() -> str | None:
    from . import sources as s_mod
    return s_mod.current_key()


def is_apinex(base_url: str | None) -> bool:
    if not base_url:
        return False
    return HOST in base_url.lower()


def _read_exports(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    out: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line.startswith("export "):
            continue
        rest = line[len("export "):].strip()
        if "=" not in rest:
            continue
        k, v = rest.split("=", 1)
        v = v.strip().strip("'\"")
        out[k.strip()] = v
    return out


def _key_from_claude_source() -> tuple[str, str, str] | None:
    try:
        entries = sorted(CLAUDE_SOURCE.iterdir())
    except OSError:
        return None
    for path in entries:
        if not path.is_file():
            continue
        exports = _read_exports(path)
        if not is_apinex(exports.get("ANTHROPIC_BASE_URL")):
            continue
        token = exports.get("ANTHROPIC_AUTH_TOKEN") or exports.get("ANTHROPIC_API_KEY")
        if token:
            return token, exports.get("ANTHROPIC_MODEL", ""), str(path)
    return None


def load_credentials() -> tuple[str, str, str] | None:
    if is_apinex(os.environ.get("ANTHROPIC_BASE_URL")):
        token = (
            os.environ.get("ANTHROPIC_AUTH_TOKEN")
            or os.environ.get("ANTHROPIC_API_KEY")
            or ""
        )
        if token:
            return token, os.environ.get("ANTHROPIC_MODEL", ""), "environment"

    exports = _read_exports(PROFILE)
    token = exports.get("ANTHROPIC_AUTH_TOKEN") or exports.get("ANTHROPIC_API_KEY")
    if token:
        return token, exports.get("ANTHROPIC_MODEL", ""), str(PROFILE)

    found = _key_from_claude_source()
    if found:
        return found
    return None


def save_key(token: str, model: str = "") -> Path:
    PROFILE.parent.mkdir(parents=True, exist_ok=True)
    body = (
        f"# Radnex — APInex profile\n"
        f'export ANTHROPIC_BASE_URL="{DEFAULT_BASE_URL}"\n'
        f'export ANTHROPIC_AUTH_TOKEN="{token}"\n'
        f'export ANTHROPIC_MODEL="{model}"\n'
        f'export ANTHROPIC_API_KEY=""\n'
    )
    fd = os.open(PROFILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(body)
    try:
        os.chmod(PROFILE, 0o600)
    except OSError:
        pass
    return PROFILE


def has_key() -> bool:
    return load_credentials() is not None


def default_free_model(token: str = "") -> str:
    return "deepseek-v4.1-flash"


def apply_to(cfg) -> tuple[str, str] | None:
    creds = load_credentials()
    if creds is None:
        return None
    token, model, origin = creds
    cfg.base_url = DEFAULT_BASE_URL
    cfg.auth_token = token
    cfg.api_key = ""
    if not model:
        model = default_free_model(token)
    if model:
        cfg.model = model
    return origin, model


def applies_to_default_endpoint(base_url: str | None) -> bool:
    url = (base_url or "").strip()
    return not url or "localhost:" in url or "127.0.0.1:" in url or is_apinex(url)


_CACHE: dict[str, tuple[list[Model], float]] = {}


def fetch_models(token: str = "", *, timeout: float = 15.0) -> tuple[list[Model] | None, str]:
    token = token.strip()
    hit = _CACHE.get(token)
    if hit and (time.monotonic() - hit[1]) < CACHE_TTL:
        return list(hit[0]), ""

    # Catalog endpoint
    url = f"{DEFAULT_BASE_URL}/v1/models"
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Radnex/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception as exc:
        fallback = [
            Model(id=m, label=m, tools=True, free=True) for m in PREFERRED_FREE_MODELS
        ]
        return fallback, f"cached default: {exc}"

    entries = data.get("data", []) if isinstance(data, dict) else []
    models: list[Model] = []
    for e in entries:
        mid = e.get("id") or ""
        if not mid:
            continue
        is_free = mid.endswith(FREE_SUFFIXES) or "free" in mid.lower()
        models.append(
            Model(
                id=mid,
                label=e.get("description", mid),
                tools=True,
                free=is_free,
                context_length=e.get("context_window", 128000),
            )
        )

    if not models:
        models = [Model(id=m, label=m, tools=True, free=True) for m in PREFERRED_FREE_MODELS]

    _CACHE[token] = (models, time.monotonic())
    return list(models), ""


def free_models(token: str = "") -> tuple[list[Model] | None, str]:
    models, err = fetch_models(token)
    if models is None:
        return None, err
    return [m for m in models if m.free], ""


def usable_free_models(token: str = "") -> tuple[list[Model] | None, str]:
    models, err = free_models(token)
    if models is None:
        return None, err
    return [m for m in models if m.chat], ""


def model_ids(token: str = "") -> tuple[list[str] | None, str]:
    models, err = fetch_models(token)
    if models is None:
        return None, err
    return [m.id for m in models if m.chat], ""


def cached_models() -> list[Model] | None:
    if not _CACHE:
        return None
    newest = max(_CACHE.values(), key=lambda x: x[1])
    if (time.monotonic() - newest[1]) >= CACHE_TTL:
        return None
    return list(newest[0])


def cached_ids() -> list[str] | None:
    models = cached_models()
    if not models:
        return None
    return [m.id for m in models if m.chat]
