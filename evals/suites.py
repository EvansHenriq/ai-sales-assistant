"""Offline evaluation suites.

- Guardrails (injection + PII): fully deterministic, no LLM required.
- Qualification: runs the qualification service against labelled conversations.
- RAG: retrieval recall@k against labelled questions.

Each suite accepts an optional in-memory ``dataset`` (used by tests); otherwise
it loads the bundled JSON dataset.
"""

import json
from pathlib import Path
from typing import Any

from app.agent.types import ChatMessage, Role, StructuredLLMClient
from app.guardrails.pii import redact_pii
from app.guardrails.prompt_injection import detect_injection
from app.qualification.service import QualificationService
from app.rag.types import Retriever
from evals.metrics import accuracy, binary_metrics

_DATASETS = Path(__file__).parent / "datasets"

Dataset = list[dict[str, Any]]


def load_dataset(name: str) -> Dataset:
    data: Dataset = json.loads((_DATASETS / f"{name}.json").read_text(encoding="utf-8"))
    return data


def run_injection_suite(dataset: Dataset | None = None) -> dict[str, float]:
    data = dataset if dataset is not None else load_dataset("guardrails_injection")
    y_true = [bool(item["is_injection"]) for item in data]
    y_pred = [detect_injection(str(item["text"])).is_injection for item in data]
    metrics = binary_metrics(y_true, y_pred)
    return {
        "samples": float(len(data)),
        "precision": metrics.precision,
        "recall": metrics.recall,
        "f1": metrics.f1,
        "accuracy": metrics.accuracy,
    }


def run_pii_suite(dataset: Dataset | None = None) -> dict[str, float]:
    data = dataset if dataset is not None else load_dataset("guardrails_pii")
    correct = 0
    for item in data:
        found = set(redact_pii(str(item["text"])).found)
        expected = set(item["expected_types"])
        if found == expected:
            correct += 1
    return {"samples": float(len(data)), "accuracy": correct / len(data) if data else 0.0}


async def run_qualification_suite(
    llm: StructuredLLMClient, *, dataset: Dataset | None = None, model: str | None = None
) -> dict[str, float]:
    data = dataset if dataset is not None else load_dataset("qualification")
    service = QualificationService(llm, model=model)
    y_true: list[str] = []
    y_pred: list[str] = []
    for item in data:
        messages = [
            ChatMessage(role=_as_role(turn["role"]), content=str(turn["content"]))
            for turn in item["conversation"]
        ]
        result, _usage = await service.qualify(messages)
        y_true.append(str(item["expected_stage"]))
        y_pred.append(result.stage.value)
    return {"samples": float(len(data)), "stage_accuracy": accuracy(y_true, y_pred)}


async def run_rag_suite(
    retriever: Retriever, *, dataset: Dataset | None = None, k: int = 4
) -> dict[str, float]:
    data = dataset if dataset is not None else load_dataset("rag")
    hits = 0
    for item in data:
        results = await retriever.search(str(item["question"]), k=k)
        if str(item["expected_source"]) in {chunk.source for chunk in results}:
            hits += 1
    return {"samples": float(len(data)), "recall_at_k": hits / len(data) if data else 0.0}


def _as_role(value: object) -> Role:
    return "assistant" if value == "assistant" else "user"
