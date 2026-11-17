# Implementation plan: Request 021

## Scope

Fix the two confirmed Spotisaver issues without changing queue behavior, browser defaults, track matching, archive validation rules, or the download provider interface.

## 1. Make the Windows diagnostic log path package independent

- Change the Windows log root from `LOCALAPPDATA` to a stable user profile location that Microsoft Store Python does not redirect.
- Use `Path.home() / "TKKGDownloader" / "logs"`, resulting in `%USERPROFILE%\TKKGDownloader\logs`.
- Keep the existing macOS and Linux XDG state directory behavior unchanged.
- Continue creating the directory recursively and verifying that the log file exists.
- Log the resolved absolute path so diagnostics show the actual location.
- Update README and Knowledge Base documentation wherever the old Windows path is documented.
- Add tests proving Windows path selection ignores `LOCALAPPDATA` and uses the user profile, while non-Windows behavior remains unchanged.

## 2. Use the Chromium download file when CDP is active

- Inspect the existing CDP download event state and the exact point where the Playwright download event is received.
- When CDP is active and reports the correlated download as completed, do not call `download.save_as()`.
- Resolve the expected file in the configured Chromium download directory using the sanitized suggested filename.
- Wait for the file to appear and its size to remain stable across consecutive checks. Require a nonzero size and enforce a bounded timeout.
- If CDP reports completion but the expected file never appears, or remains empty or unstable until timeout, raise a clear diagnostic error. Do not silently switch to Playwright's temporary artifact after CDP claims completion.
- When CDP is unavailable, preserve the existing Playwright `download.save_as()` fallback.
- Keep the existing final file existence and nonzero size checks, then continue into the unchanged archive validation workflow.
- Ensure CDP detach still happens on success and failure.

## 3. Tests

Add focused tests for:
- CDP active, correlated download completed, file exists: use the Chromium file and never call `save_as()`.
- CDP active, file appears after a short delay: wait and accept once stable.
- CDP active, missing, empty, or persistently changing file: fail with an actionable timeout.
- CDP unavailable: call `save_as()` and retain existing behavior.
- CDP download event correlation and suggested filename handling remain correct.
- Windows log directory resolves under the user profile and does not use `LOCALAPPDATA`.
- Non-Windows log directory remains under XDG state or the existing home fallback.

Use deterministic mocks and temporary directories. Do not perform a live Spotisaver download in automated tests.

## 4. Documentation

- Update the README Windows diagnostic log location.
- Update the relevant Knowledge Base entry and request implementation record.
- Explain that CDP owns file persistence when available and Playwright owns it only in fallback mode.

## 5. Verification

- Run the complete unit test suite.
- Run Python compilation checks.
- Run the TKKGData contract smoke test.
- Inspect the final diff for unintended changes.
- Do not merge until the user explicitly approves after review.

## Acceptance criteria

- A successful CDP transfer no longer depends on Playwright's temporary artifact being available.
- A completed ZIP is not handed to archive validation until the file is present, nonempty, and stable.
- Playwright fallback remains functional when CDP is unavailable.
- On Windows, logs are directly accessible at `%USERPROFILE%\TKKGDownloader\logs`, including with Microsoft Store Python.
- All relevant tests and repository checks pass.
