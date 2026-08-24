# P0 evaluator definitions

Evaluator version: `p0-event-metrics/1.0.0`.

- Time tolerance is inclusive: distance `<= 0.050000` seconds matches. Tests pin `t-ε`, `t`, and
  `t+ε`.
- Matching is global-nearest one-to-one with stable reference/prediction index tie-breaking. A
  second prediction near an already matched reference is a false positive.
- Time precision is `TP/(TP+FP)` and recall is `TP/(TP+FN)`. Deleting predictions therefore lowers
  recall without penalizing precision; inserting predictions lowers precision without increasing
  recall.
- Class/pitch matching applies the same one-to-one time rule and additionally requires the exact
  drum class or pitch-class label.
- Per-class metrics cover the union of classes in truth and prediction. Micro metrics sum class
  TP/FP/FN before division; macro metrics average each present class's result.
- Empty truth with empty prediction returns precision/recall/F1 `1`. Empty prediction with nonempty
  truth returns precision `1`, recall `0`, and F1 `0`. A class absent from both sets is omitted from
  macro averaging.
- Every numeric input and output must be finite. NaN, Infinity, negative time/tolerance, and divide
  by zero are rejected or receive the documented finite empty-set value; none can pass the gate.

These controls validate evaluator behavior on transparent synthetic data only. They are not
real-song accuracy, separation, transcription, arrangement, perceptual-quality, or holdout
evidence.
