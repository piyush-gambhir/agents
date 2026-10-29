# Dependency security

The fork's dependency alerts were previously disabled. Enabling them exposed 172 advisories in the existing workspace lockfile. These are dependency findings, not false positives to dismiss in bulk.

The updated lockfile uses patched releases for the affected Python dependencies. The core manifest also moves its pinned JSON repair library and coupled OpenTelemetry packages to patched releases. Comparing the original alert ranges with the new locked versions leaves no matches. Auditing the exported resolved dependencies with pip-audit also reports no known vulnerabilities.

## Speechmatics compatibility

The Speechmatics 0.2.8 `smart` extra caps Transformers below v5. The plugin now declares the same Smart Turn dependencies directly, using patched Transformers 5.10 or later, rather than requesting that capped extra. There is no global resolver override and no provider feature is removed.

`tests/test_speechmatics_feature_extractor.py` exercises the SDK's actual SmartTurnDetector feature-extraction path with synthetic audio and a fake ONNX session. It verifies finite float32 features of the expected shape and the returned prediction. It does not download a model or call a provider. The normal model inference and remote STT integrations still need their existing integration coverage.

The required Security checks gate includes a frozen dependency export and pip-audit, plus this offline compatibility regression. Alerts on the default branch remain open until the PR is merged and GitHub refreshes its dependency graph.

Made by gpt-6 in Codex
