"""Offline semantic answer judging with the bundled Ruri v3 INT8 model."""

from __future__ import annotations

import hashlib
import json
import os
import re
import threading
import unicodedata
from typing import Any


MODEL_REVISION = "5c329c35a623f38804d1b048dfa61b9f5818d8b4"
JUDGE_NAME = "ruri-v3-30m-int8"
DEFAULT_CORRECT_THRESHOLD = 0.95
DEFAULT_BORDERLINE_THRESHOLD = 0.90
DEFAULT_HARD_NEGATIVE_THRESHOLD = 0.994


class SemanticJudgeUnavailable(RuntimeError):
    """Raised when the local model or its runtime dependencies cannot load."""


class SemanticAnswerJudge:
    """Judge short Japanese answers without making any network requests.

    The converted ONNX graph returns token embeddings for the first item in a
    batch, so inputs are intentionally evaluated one at a time and mean-pooled
    exactly as the upstream SentenceTransformer model specifies.
    """

    def __init__(self, project_root: str):
        self.model_dir = os.path.join(project_root, "models", "ruri-v3-30m-int8")
        self.model_path = os.path.join(self.model_dir, "model_int8.onnx")
        self.tokenizer_path = os.path.join(self.model_dir, "tokenizer.model")
        self._session = None
        self._tokenizer = None
        self._np = None
        self._load_lock = threading.Lock()
        self._embedding_cache: dict[str, Any] = {}

    @staticmethod
    def normalize(text: str) -> str:
        normalized = unicodedata.normalize("NFKC", str(text)).lower()
        return re.sub(r"[\s、。,.!！?？・「」『』()（）]+", "", normalized)

    @staticmethod
    def judge_version(definition: dict[str, Any]) -> str:
        semantic_config = definition.get("semantic_judge") or {}
        versioned_data = {
            "canonical_answer": definition.get("canonical_answer", ""),
            "accepted_answers": definition.get("accepted_answers", []),
            "semantic_judge": semantic_config,
        }
        encoded = json.dumps(
            versioned_data, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        config_hash = hashlib.sha256(encoded).hexdigest()[:12]
        return f"{JUDGE_NAME}-{MODEL_REVISION[:8]}-{config_hash}"

    def judge(self, definition: dict[str, Any], answer_text: str) -> dict[str, Any]:
        config = definition.get("semantic_judge") or {}
        version = self.judge_version(definition)
        canonical = str(definition.get("canonical_answer", "")).strip()
        if not canonical:
            return {
                "result": "error",
                "confidence": 0.0,
                "judge_version": version,
                "reason_codes": ("missing_canonical_answer",),
            }

        answer_normalized = self.normalize(answer_text)
        normalized_text = unicodedata.normalize("NFKC", str(answer_text))
        for pattern in config.get("reject_patterns", []):
            try:
                rejected = re.search(str(pattern), normalized_text, re.IGNORECASE)
            except re.error as exc:
                return {
                    "result": "error",
                    "confidence": 0.0,
                    "judge_version": version,
                    "reason_codes": ("invalid_reject_pattern",),
                    "error_detail": str(exc),
                }
            if rejected:
                return {
                    "result": "incorrect",
                    "confidence": 1.0,
                    "judge_version": version,
                    "reason_codes": ("reject_pattern_match",),
                    "semantic_score": 0.0,
                }

        exact_answers = [canonical, *definition.get("accepted_answers", [])]
        if answer_normalized and answer_normalized in {
            self.normalize(value) for value in exact_answers
        }:
            return {
                "result": "correct",
                "confidence": 1.0,
                "judge_version": version,
                "reason_codes": ("exact_answer",),
                "semantic_score": 1.0,
            }

        hard_negatives = [
            str(value).strip()
            for value in config.get("hard_negatives", [])
            if str(value).strip()
        ]
        positive_examples = [
            str(value).strip()
            for value in config.get("positive_examples", [])
            if str(value).strip()
        ]
        if answer_normalized and answer_normalized in {
            self.normalize(value) for value in hard_negatives
        }:
            return {
                "result": "incorrect",
                "confidence": 1.0,
                "judge_version": version,
                "reason_codes": ("exact_hard_negative",),
                "semantic_score": 0.0,
                "hard_negative_score": 1.0,
            }

        try:
            answer_vector = self._encode(answer_text)
            positive_score = max(
                self._cosine(answer_vector, self._encode(text))
                for text in [canonical, *positive_examples]
            )
            negative_score = max(
                (self._cosine(answer_vector, self._encode(text)) for text in hard_negatives),
                default=0.0,
            )
        except Exception as exc:
            return {
                "result": "error",
                "confidence": 0.0,
                "judge_version": version,
                "reason_codes": ("model_unavailable",),
                "error_detail": str(exc),
            }

        correct_threshold = float(
            config.get("correct_threshold", DEFAULT_CORRECT_THRESHOLD)
        )
        borderline_threshold = float(
            config.get("borderline_threshold", DEFAULT_BORDERLINE_THRESHOLD)
        )
        hard_negative_threshold = float(
            config.get("hard_negative_threshold", DEFAULT_HARD_NEGATIVE_THRESHOLD)
        )

        if negative_score >= hard_negative_threshold:
            result = "incorrect"
            reason = "hard_negative_match"
            confidence = negative_score
        elif negative_score > positive_score:
            result = "incorrect"
            reason = "hard_negative_nearer"
            confidence = negative_score
        elif positive_score >= correct_threshold:
            result = "correct"
            reason = "semantic_match"
            confidence = positive_score
        elif positive_score >= borderline_threshold:
            result = "borderline"
            reason = "semantic_borderline"
            confidence = positive_score
        else:
            result = "incorrect"
            reason = "semantic_mismatch"
            confidence = 1.0 - positive_score

        return {
            "result": result,
            "confidence": float(confidence),
            "judge_version": version,
            "reason_codes": (reason,),
            "semantic_score": float(positive_score),
            "hard_negative_score": float(negative_score),
        }

    def _load(self) -> None:
        if self._session is not None:
            return
        with self._load_lock:
            if self._session is not None:
                return
            if not os.path.isfile(self.model_path):
                raise SemanticJudgeUnavailable(f"ONNX model not found: {self.model_path}")
            if not os.path.isfile(self.tokenizer_path):
                raise SemanticJudgeUnavailable(
                    f"tokenizer not found: {self.tokenizer_path}"
                )
            try:
                import numpy as np
                import onnxruntime as ort
                import sentencepiece as spm
            except ImportError as exc:
                raise SemanticJudgeUnavailable(
                    "onnxruntime, sentencepiece, and numpy are required"
                ) from exc

            options = ort.SessionOptions()
            options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            self._session = ort.InferenceSession(
                self.model_path,
                sess_options=options,
                providers=["CPUExecutionProvider"],
            )
            # SentencePiece's Windows extension cannot open paths containing
            # Japanese characters reliably. Loading serialized bytes keeps the
            # workspace path out of the native filesystem API.
            with open(self.tokenizer_path, "rb") as handle:
                tokenizer_proto = handle.read()
            self._tokenizer = spm.SentencePieceProcessor(
                model_proto=tokenizer_proto
            )
            self._np = np

    def _encode(self, text: str):
        cached = self._embedding_cache.get(text)
        if cached is not None:
            return cached
        self._load()
        content_ids = self._tokenizer.encode(str(text), out_type=int)[:126]
        token_ids = [self._tokenizer.bos_id(), *content_ids, self._tokenizer.eos_id()]
        input_ids = self._np.asarray([token_ids], dtype=self._np.int64)
        attention_mask = self._np.ones_like(input_ids, dtype=self._np.int64)
        output = self._session.run(
            None,
            {"input_ids": input_ids, "attention_mask": attention_mask},
        )[0]
        if output.ndim == 3:
            output = output[0]
        if output.ndim == 2:
            vector = output.mean(axis=0)
        elif output.ndim == 1:
            vector = output
        else:
            raise SemanticJudgeUnavailable(
                f"unexpected ONNX output shape: {output.shape}"
            )
        norm = float(self._np.linalg.norm(vector))
        if norm <= 1e-12:
            raise SemanticJudgeUnavailable("model returned a zero-length embedding")
        vector = (vector / norm).astype(self._np.float32, copy=False)
        self._embedding_cache[text] = vector
        return vector

    @staticmethod
    def _cosine(left, right) -> float:
        return float(left @ right)
