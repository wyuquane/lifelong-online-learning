"""Tests for the synthetic syn1-syn4 generators."""

from __future__ import annotations

import numpy as np

from aklo.data.synthetic import make_synthetic


def test_deterministic_for_same_seed() -> None:
    first = make_synthetic("syn1", n_tasks=6, n_samples=15, seed=3)
    second = make_synthetic("syn1", n_tasks=6, n_samples=15, seed=3)
    assert [task.task_id for task in first.tasks] == [
        task.task_id for task in second.tasks
    ]
    for left, right in zip(first.tasks, second.tasks):
        np.testing.assert_array_equal(left.X_train, right.X_train)
        np.testing.assert_array_equal(left.y_train, right.y_train)


def test_different_seed_changes_data() -> None:
    first = make_synthetic("syn1", n_tasks=2, n_samples=10, seed=0)
    second = make_synthetic("syn1", n_tasks=2, n_samples=10, seed=1)
    assert not np.array_equal(first.tasks[0].X_train, second.tasks[0].X_train)


def test_task_count_and_categories() -> None:
    stream = make_synthetic("syn1", n_tasks=7, n_samples=10, seed=0)
    assert len(stream) == 7
    assert stream.task_type == "classification"
    assert [task.category for task in stream.tasks] == [
        "D1",
        "D1",
        "D1",
        "D2",
        "D2",
        "D2",
        "D2",
    ]
    assert stream.n_features == 2


def test_nested_prefixes_for_sample_count() -> None:
    """E2 relies on the same underlying pool for different m_t."""
    short = make_synthetic("syn1", n_tasks=1, n_samples=10, seed=0)
    long = make_synthetic("syn1", n_tasks=1, n_samples=300, seed=0)
    np.testing.assert_array_equal(short.tasks[0].X_train, long.tasks[0].X_train[:10])
    np.testing.assert_array_equal(short.tasks[0].y_train, long.tasks[0].y_train[:10])


def test_syn2_reuses_d1_marginal_and_flips_d2_labels() -> None:
    """syn2 draws both classes from D1's marginal and negates D2 labels."""
    stream = make_synthetic("syn2", n_tasks=2, n_samples=200, seed=0)
    d1, d2 = stream.tasks
    assert d1.category == "D1" and d2.category == "D2"
    # Both tasks use the D1 mean [10, 10], unlike syn1's D2 mean [20, 5].
    np.testing.assert_allclose(d1.X_train.mean(axis=0), [10.0, 10.0], atol=0.4)
    np.testing.assert_allclose(d2.X_train.mean(axis=0), [10.0, 10.0], atol=0.4)
    # A classifier trained on D1 should be anti-correlated with D2 labels.
    from sklearn.linear_model import LogisticRegression

    classifier = LogisticRegression().fit(d1.X_train, d1.y_train)
    accuracy = classifier.score(d2.X_train, d2.y_train)
    assert accuracy < 0.2


def test_regression_targets_are_real_valued() -> None:
    stream = make_synthetic("syn3", n_tasks=2, n_samples=20, seed=0)
    assert stream.task_type == "regression"
    assert np.issubdtype(stream.tasks[0].y_train.dtype, np.floating)
    assert np.any(np.abs(stream.tasks[0].y_train) > 1.5)


def test_held_out_split() -> None:
    stream = make_synthetic(
        "syn1", n_tasks=3, n_samples=50, seed=0, test_fraction=0.2
    )
    for task in stream.tasks:
        assert task.X_test is not None
        assert task.y_test is not None
        assert task.n_train == 40
        assert len(task.y_test) == 10


def test_separate_test_block_is_disjoint_and_sized() -> None:
    stream = make_synthetic(
        "syn1", n_tasks=2, n_samples=100, seed=0, n_test=100
    )
    for task in stream.tasks:
        assert task.n_train == 100
        assert task.X_test is not None and task.y_test is not None
        assert len(task.y_test) == 100
        # The test rows are the next block of the same sample pool, so they
        # must not overlap with the training rows.
        train_rows = {tuple(row) for row in task.X_train}
        test_rows = {tuple(row) for row in task.X_test}
        assert train_rows.isdisjoint(test_rows)
