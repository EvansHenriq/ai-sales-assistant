"""Small, dependency-free metric helpers for the eval suites."""

from collections.abc import Sequence
from dataclasses import dataclass


def accuracy(y_true: Sequence[object], y_pred: Sequence[object]) -> float:
    if not y_true:
        return 0.0
    correct = sum(1 for true, pred in zip(y_true, y_pred, strict=True) if true == pred)
    return correct / len(y_true)


@dataclass(frozen=True)
class BinaryMetrics:
    precision: float
    recall: float
    f1: float
    accuracy: float


def binary_metrics(y_true: Sequence[bool], y_pred: Sequence[bool]) -> BinaryMetrics:
    pairs = list(zip(y_true, y_pred, strict=True))
    tp = sum(1 for true, pred in pairs if true and pred)
    fp = sum(1 for true, pred in pairs if not true and pred)
    fn = sum(1 for true, pred in pairs if true and not pred)
    tn = sum(1 for true, pred in pairs if not true and not pred)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    total = tp + fp + fn + tn
    return BinaryMetrics(
        precision=precision,
        recall=recall,
        f1=f1,
        accuracy=(tp + tn) / total if total else 0.0,
    )
