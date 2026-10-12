"""Build-time patch: preserve modality attribute through torch.split in Qwen Omni.

vLLM 0.28.0's Qwen3-Omni model calls torch.split() on multimodal embeddings
for deepstack processing. torch.split() creates new tensors that lose the
custom .modality attribute set by the V1 encoder gather, causing
``ValueError: Missing modality on multimodal embedding at index 0`` when
use_audio_in_video=True.

This patch adds a copy_mm_embedding_modality() call after the split so the
attribute survives into merge_interleaved_embeddings().

Run once during ``docker build``:
    RUN python3 /tmp/patches/omni_modality.py
"""

from __future__ import annotations

import importlib.util
import site
from pathlib import Path


def _find_thinker_py() -> Path:
    for d in site.getsitepackages() + [site.getusersitepackages()]:
        p = Path(d) / "vllm" / "model_executor" / "models" / "qwen3_omni_moe_thinker.py"
        if p.exists():
            return p
    spec = importlib.util.find_spec("vllm.model_executor.models.qwen3_omni_moe_thinker")
    if spec and spec.origin:
        return Path(spec.origin)
    raise FileNotFoundError("Cannot find qwen3_omni_moe_thinker.py")


def patch():
    f = _find_thinker_py()
    src = f.read_text()

    if "copy_mm_embedding_modality(embeddings, embeddings_main)" in src:
        print(f"[omni_modality] already patched: {f}")
        return

    old = "                    multimodal_embeddings[index] = embeddings_main"
    new = (
        "                    from vllm.multimodal.utils import copy_mm_embedding_modality\n"
        "                    copy_mm_embedding_modality(embeddings, embeddings_main)\n"
        "                    multimodal_embeddings[index] = embeddings_main"
    )

    if old not in src:
        raise RuntimeError(f"Cannot find target line in {f}")

    src = src.replace(old, new, 1)
    f.write_text(src)
    print(f"[omni_modality] patched: {f}")


if __name__ == "__main__":
    patch()
