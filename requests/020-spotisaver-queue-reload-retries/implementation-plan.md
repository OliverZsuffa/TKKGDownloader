# Implementation plan: Request 020

## 1. Inspect current implementation

Trace the existing configuration dataclass/parser, command line configuration precedence, Spotisaver queue rejection state machine, page lifecycle, and browser download event listener. Keep the implementation aligned with the current code rather than introducing a second retry mechanism.

## 2. Extend configuration

Add `queue_retry_interval_seconds` and `queue_reload_after_retries` to the resolved configuration model.

- Defaults: 25 seconds and 5 retries.
- Parse both as positive integers from TOML.
- Explicitly reject booleans, since Python treats bool as a subclass of int.
- Preserve current precedence: CLI arguments, config file, built-in defaults. No new CLI flags are required for this request unless the existing architecture makes them necessary.
- Keep older config files valid when the keys are absent.
- Update configuration unit tests for defaults, overrides, invalid values, and precedence.

## 3. Update queue retry state machine

Keep the current strict distinction between explicit rejection, unconfirmed state, and positive processing evidence.

For each explicit queue rejection:
1. Wait for the configured interval.
2. Confirm the rejection is still active.
3. Close the rejection modal and confirm it has closed.
4. Verify the real download button is visible and enabled.
5. Retry the album request.
6. Count this as an unsuccessful retry only if the retry is explicitly rejected again.

When the configured number of consecutive retry attempts has been explicitly rejected, switch recovery strategy:
1. Reload the current album page.
2. Verify the resulting URL still identifies the expected album.
3. Re-establish page readiness using the existing button-first polling behaviour.
4. Click the real download button only when it is visible and enabled.
5. Reset the consecutive retry counter after the reload and resume normal queue monitoring.

Do not count provisional or unconfirmed states as rejections. Do not reload for generic errors or slow processing. Avoid duplicate clicks during navigation or reload.

## 4. Preserve browser download monitoring

Inspect the existing CDP download event subscription and ensure its lifecycle is not tied to a page document that is destroyed by navigation. Keep the browser-context level download listener active across page reloads. Confirm that download GUID correlation and ZIP progress handling continue to work after the reload path.

If the current implementation cannot safely preserve the listener, restructure its lifecycle minimally and cover it with a regression test.

## 5. Documentation

Update the README configuration section with both new keys, defaults, validation behaviour, and an example. Explain that the reload threshold counts consecutive retries that were themselves explicitly rejected, and that the counter resets after a page reload.

## 6. Verification

Add deterministic mocked tests for:
- Defaults of 25 seconds and 5 retries.
- TOML overrides and validation, including bool rejection.
- Existing config compatibility.
- Configured wait duration.
- Normal modal-close retry behaviour below the threshold.
- Full page reload at the threshold.
- Album URL and button readiness validation after reload.
- Retry counter reset after reload.
- No retry or reload on unconfirmed states or generic errors.
- Browser download event listener remaining active across reload.
- ZIP download event handling after reload.

Run Python compilation, the full unit test suite, and the TKKGData contract smoke test. Do not perform a live download. Record test results in the request notes and open a PR for review. Do not merge until explicitly approved.
