from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping, Sequence, Set, Tuple


METRIC_VERSION = "p0-event-metrics/1.0.0"


def _ratio(numerator: int, denominator: int, empty_value: float) -> float:
    if denominator == 0:
        return empty_value
    return float(numerator) / float(denominator)


def _scores(tp: int, fp: int, fn: int) -> Dict[str, float]:
    precision = _ratio(tp, tp + fp, 1.0)
    recall = _ratio(tp, tp + fn, 1.0)
    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2.0 * precision * recall / (precision + recall)
    return {"precision": precision, "recall": recall, "f1": f1}


def _match(
    reference: Sequence[Mapping[str, Any]],
    prediction: Sequence[Mapping[str, Any]],
    tolerance_seconds: float,
    require_same_class: bool,
) -> List[Tuple[int, int]]:
    candidates: List[Tuple[float, int, int]] = []
    for reference_index, expected in enumerate(reference):
        for prediction_index, observed in enumerate(prediction):
            if require_same_class and expected.get("class") != observed.get("class"):
                continue
            distance = abs(float(expected["onset_seconds"]) - float(observed["onset_seconds"]))
            if distance <= tolerance_seconds + 1e-12:
                candidates.append((distance, reference_index, prediction_index))
    candidates.sort(key=lambda item: (item[0], item[1], item[2]))
    matched_reference: Set[int] = set()
    matched_prediction: Set[int] = set()
    matches: List[Tuple[int, int]] = []
    for _, reference_index, prediction_index in candidates:
        if reference_index in matched_reference or prediction_index in matched_prediction:
            continue
        matched_reference.add(reference_index)
        matched_prediction.add(prediction_index)
        matches.append((reference_index, prediction_index))
    return matches


def evaluate_events(
    reference: Sequence[Mapping[str, Any]],
    prediction: Sequence[Mapping[str, Any]],
    tolerance_seconds: float = 0.05,
) -> Dict[str, Any]:
    if not isinstance(reference, (list, tuple)) or not isinstance(prediction, (list, tuple)):
        raise TypeError("reference and prediction must be sequences")
    if not isinstance(tolerance_seconds, (int, float)) or not math.isfinite(float(tolerance_seconds)) or tolerance_seconds < 0:
        raise ValueError("tolerance_seconds must be finite and non-negative")
    for collection_name, collection in (("reference", reference), ("prediction", prediction)):
        for index, event in enumerate(collection):
            onset = event.get("onset_seconds")
            if not isinstance(onset, (int, float)) or not math.isfinite(float(onset)) or onset < 0:
                raise ValueError("%s[%d].onset_seconds must be finite and non-negative" % (collection_name, index))
            if not isinstance(event.get("class"), str) or not event.get("class"):
                raise ValueError("%s[%d].class must be a non-empty string" % (collection_name, index))

    onset_matches = _match(reference, prediction, float(tolerance_seconds), require_same_class=False)
    tp = len(onset_matches)
    fp = len(prediction) - tp
    fn = len(reference) - tp
    onset_scores = _scores(tp, fp, fn)

    class_matches = _match(reference, prediction, float(tolerance_seconds), require_same_class=True)
    class_tp = len(class_matches)
    class_fp = len(prediction) - class_tp
    class_fn = len(reference) - class_tp
    class_scores = _scores(class_tp, class_fp, class_fn)

    classes = sorted({item["class"] for item in reference} | {item["class"] for item in prediction})
    per_class: Dict[str, Dict[str, Any]] = {}
    for class_name in classes:
        class_reference = [item for item in reference if item["class"] == class_name]
        class_prediction = [item for item in prediction if item["class"] == class_name]
        matches = _match(class_reference, class_prediction, float(tolerance_seconds), require_same_class=True)
        class_counts = {
            "tp": len(matches),
            "fp": len(class_prediction) - len(matches),
            "fn": len(class_reference) - len(matches),
        }
        class_counts.update(_scores(class_counts["tp"], class_counts["fp"], class_counts["fn"]))
        per_class[class_name] = class_counts

    if per_class:
        macro = {
            name: sum(item[name] for item in per_class.values()) / len(per_class)
            for name in ("precision", "recall", "f1")
        }
    else:
        macro = {"precision": 1.0, "recall": 1.0, "f1": 1.0}

    result: Dict[str, Any] = {
        "metric_version": METRIC_VERSION,
        "tolerance_seconds": float(tolerance_seconds),
        "tolerance_rule": "inclusive",
        "matching_rule": "global-nearest one-to-one; stable index tie-break",
        "empty_set_policy": "empty/empty=1; empty prediction against non-empty truth has precision=1 and recall=0",
        "empty_class_policy": "classes in reference-or-prediction; empty/empty class omitted",
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": onset_scores["precision"],
        "recall": onset_scores["recall"],
        "f1": onset_scores["f1"],
        "class_tp": class_tp,
        "class_fp": class_fp,
        "class_fn": class_fn,
        "class_precision": class_scores["precision"],
        "class_recall": class_scores["recall"],
        "class_f1": class_scores["f1"],
        "per_class": per_class,
        "micro": dict(class_scores),
        "macro": macro,
    }
    for key, value in result.items():
        if isinstance(value, float) and not math.isfinite(value):
            raise ArithmeticError("non-finite evaluator output at %s" % key)
    return result
