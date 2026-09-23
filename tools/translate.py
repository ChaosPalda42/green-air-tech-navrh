"""C-007: Překlad obsahu lokálním modelem (CZ -> EN/DE)."""
from __future__ import annotations

import json
import os
import re
import sys
from typing import Any

LANGS: dict[str, str] = {"en": "English", "de": "German"}


# ---------------------------------------------------------------------------
# LocalClient
# ---------------------------------------------------------------------------

class LocalClient:
    """HTTP client for a local model server (loopback only)."""

    def __init__(self, base_url: str, model: str, timeout: float = 600.0) -> None:
        # Verify loopback
        from urllib.parse import urlparse

        parsed = urlparse(base_url)
        host = parsed.hostname or ""
        if host not in ("localhost", "127.0.0.1", "::1"):
            raise ValueError(
                f"base_url host '{host}' is not loopback. "
                "Production data must not leave this machine."
            )
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def complete(self, prompt: str, **kwargs: Any) -> str:
        import httpx

        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }
        resp = httpx.post(url, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError("No choices in response")
        return choices[0]["message"]["content"]


# ---------------------------------------------------------------------------
# chunk_strings
# ---------------------------------------------------------------------------

def chunk_strings(flat: dict[str, str], max_chars: int) -> list[dict[str, str]]:
    """Split a flat dict into batches whose total value lengths ≤ max_chars."""
    if not flat:
        return []

    chunks: list[dict[str, str]] = []
    current: dict[str, str] = {}
    current_len = 0

    for key, value in flat.items():
        val_len = len(value)
        if not current or current_len + val_len > max_chars:
            if current:
                chunks.append(current)
            current = {key: value}
            current_len = val_len
        else:
            current[key] = value
            current_len += val_len

    if current:
        chunks.append(current)

    return chunks


# ---------------------------------------------------------------------------
# protect_placeholders / restore_placeholders
# ---------------------------------------------------------------------------

def protect_placeholders(text: str) -> tuple[str, dict[str, str]]:
    """Replace every {…} with @@n@@ placeholders."""
    placeholders: dict[str, str] = {}
    counter = [0]

    def _replacer(m: re.Match) -> str:
        original = m.group(0)
        placeholder = f"@@{counter[0]}@@"
        placeholders[placeholder] = original
        counter[0] += 1
        return placeholder

    protected = re.sub(r"\{[^}]+\}", _replacer, text)
    return protected, placeholders


def restore_placeholders(text: str, mapa: dict[str, str]) -> str:
    """Restore @@n@@ placeholders back to original {…}."""
    for placeholder, original in mapa.items():
        text = text.replace(placeholder, original)
    return text


# ---------------------------------------------------------------------------
# build_prompt
# ---------------------------------------------------------------------------

def build_prompt(
    chunk: dict[str, str], target: str, glossary: dict[str, str]
) -> str:
    """Build an English-language translation prompt."""
    target_lang = LANGS[target]
    lines: list[str] = []
    lines.append(
        "You are a professional translator for a technical company. "
        "Translate the following Czech values into "
        f"{target_lang}. Keep keys unchanged. "
        "Preserve placeholder tokens like @@0@@ exactly as they are. "
        "Respond with ONLY a single JSON object — no other text."
    )

    if glossary:
        glossary_lines = " ".join(
            f"{k} → {v}" for k, v in glossary.items()
        )
        lines.append(
            f"Glossary (use these preferred translations): {glossary_lines}"
        )

    lines.append("Maintain a professional, factual tone appropriate for a technical company.")
    lines.append("")
    lines.append("Translate the following key-value pairs:")

    for key, value in chunk.items():
        lines.append(f'  "{key}": "{value}"')

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# parse_response
# ---------------------------------------------------------------------------

def parse_response(text: str, chunk: dict[str, str]) -> dict[str, str]:
    """Extract a JSON object from the model response."""
    # Try to find JSON object — strip markdown code blocks first
    cleaned = text.strip()

    # Remove ```json ... ``` wrapper
    m = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?```", cleaned)
    if m:
        cleaned = m.group(1).strip()

    # Find the first { and last } that form a valid JSON object
    obj_match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", cleaned)
    if not obj_match:
        raise ValueError("No JSON object found in response")

    json_str = obj_match.group(0)

    try:
        result = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON: {e}") from e

    if not isinstance(result, dict):
        raise ValueError("Response is not a JSON object")

    # Check all required keys are present
    for key in chunk:
        if key not in result:
            raise ValueError(f"Missing key '{key}' in response")

    # Return only the required keys, converted to str
    return {key: str(result[key]) for key in chunk}


# ---------------------------------------------------------------------------
# translate_flat
# ---------------------------------------------------------------------------

def translate_flat(
    flat: dict[str, str],
    target: str,
    client: LocalClient,
    max_chars: int = 4000,
    pokusy: int = 2,
    glossary: dict[str, str] | None = None,
) -> dict[str, str]:
    """Translate a flat dictionary of Czech strings."""
    if glossary is None:
        glossary = {}

    result: dict[str, str] = {}

    # Separate empty values (skip translation)
    to_translate: dict[str, str] = {}
    for key, value in flat.items():
        if value.strip() == "":
            result[key] = value
        else:
            to_translate[key] = value

    if not to_translate:
        return result

    # Chunk the non-empty values
    chunks = chunk_strings(to_translate, max_chars)

    for chunk in chunks:
        # Protect placeholders in values
        protected_values: dict[str, str] = {}
        all_placeholders: dict[str, str] = {}
        for key, value in chunk.items():
            protected, ph = protect_placeholders(value)
            protected_values[key] = protected
            all_placeholders.update(ph)

        # Try translating with retries
        translated: dict[str, str] | None = None
        for attempt in range(pokusy):
            prompt = build_prompt(protected_values, target, glossary)
            try:
                response = client.complete(prompt)
                translated = parse_response(response, protected_values)
                break
            except ValueError:
                if attempt == pokusy - 1:
                    # Last attempt failed — keep original values
                    translated = None
                continue

        if translated is None:
            # Failed all attempts — use original values
            translated = dict(chunk)

        # Restore placeholders in translated values
        for key in translated:
            translated[key] = restore_placeholders(
                translated[key], all_placeholders
            )

        result.update(translated)

    return result


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _flatten(obj: Any, prefix: str = "") -> dict[str, str]:
    """Recursively flatten a nested dict into dot-separated keys, stringifying values."""
    items: dict[str, str] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, (dict, list)):
                items.update(_flatten(v, new_key))
            else:
                items[new_key] = str(v)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            new_key = f"{prefix}.{i}" if prefix else str(i)
            if isinstance(v, (dict, list)):
                items.update(_flatten(v, new_key))
            else:
                items[new_key] = str(v)
    else:
        items[prefix] = str(obj)
    return items


def _unflatten(flat: dict[str, str]) -> dict[str, Any]:
    """Restore a dot-flattened dict back to nested structure."""
    result: dict[str, Any] = {}
    for key, value in flat.items():
        parts = key.split(".")
        d = result
        for part in parts[:-1]:
            if part not in d or not isinstance(d[part], dict):
                d[part] = {}
            d = d[part]
        d[parts[-1]] = value
    return result


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <input.json> <output.json> <en|de>", file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    target = sys.argv[3]

    if target not in LANGS:
        print(f"Unsupported target language: {target}. Use en or de.", file=sys.stderr)
        sys.exit(1)

    # Load input JSON
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Flatten
    flat = _flatten(data)

    # Create client from environment
    base_url = os.environ.get("FACTORY_BASE_URL", "http://127.0.0.1:8080/v1")
    model = os.environ.get("FACTORY_MODEL", "qwen3.8-flash-next")
    client = LocalClient(base_url=base_url, model=model)

    # Translate
    translated_flat = translate_flat(flat, target, client)

    # Unflatten and write
    result = _unflatten(translated_flat)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Translated {len(translated_flat)} keys -> {output_path}")
