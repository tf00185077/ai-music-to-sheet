# Verifying P0

Prerequisites are Git, POSIX `sh`, and Python 3.9 or newer. There are no downloaded or third-party
runtime dependencies.

Run from a clean checkout:

```sh
./scripts/verify-p0 --output artifacts/p0/latest
```

The runner reads `p0/expected-checks.json`, discovers the required acceptance tests, and requires
the exact nonempty sets to match. A failure, error, unexpected success, expected failure, skip,
missing check, missing output, corrupt fixture, incompatible annotation, dirty pre-run tree,
non-finite metric, low score, invalid report, or unresolved evidence produces a nonzero exit.

The success output contains:

- `process-test-report.json` — aggregate A–G gate record with exact candidate SHA and dirty flag;
- `evaluation-transcription.json` and `evaluation-arrangement.json` — distinct scored artifacts,
  both checksum-cross-linked by the process report;
- `provenance-index.json` — every direct/indirect ancestor, hash, type, and store path;
- `samples/` — key SourceMedia and two-mode TrackIR examples;
- `verify.log` — the complete discovered-test execution record;
- `artifact-store/` and `modes/` — real serialized intermediate artifacts.

Failures still preserve `process-test-report.json` and `verify.log` with one of the six failure
families and a reason. CI runs the identical command and uploads `artifacts/p0/latest` even when the
verification step fails; missing evidence makes artifact upload fail too.

Fixture version `p0-fixtures/1.0.0` is transparent validation data. The manifest is locked by
`fixtures/p0/manifest-lock.json`, outside the version directory. Editing a fixture and its inner
manifest under the same version therefore still breaks the external lock. Any legitimate fixture
change requires a new version and lock entry.
