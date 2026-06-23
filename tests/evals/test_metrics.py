from evals.metrics import accuracy, binary_metrics


def test_accuracy() -> None:
    assert accuracy(["a", "b", "c"], ["a", "x", "c"]) == 2 / 3
    assert accuracy([], []) == 0.0


def test_binary_metrics() -> None:
    # tp=1, fp=1, fn=1, tn=1
    metrics = binary_metrics([True, True, False, False], [True, False, False, True])
    assert metrics.precision == 0.5
    assert metrics.recall == 0.5
    assert metrics.f1 == 0.5
    assert metrics.accuracy == 0.5


def test_binary_metrics_perfect() -> None:
    metrics = binary_metrics([True, False], [True, False])
    assert metrics.precision == 1.0
    assert metrics.recall == 1.0
    assert metrics.accuracy == 1.0
