# Request 020: Configurable Spotisaver queue retries and page reload

## Goal

Make Spotisaver queue recovery configurable and add a full page reload as a second recovery strategy when repeated queue retries do not acquire a download slot.

## Expected behaviour

1. The default wait after an explicit "all download slots are busy" rejection is 25 seconds instead of 30 seconds.
2. The wait interval is configurable in the user TOML configuration file.
3. After a configurable number of unsuccessful queue retry attempts, the provider reloads the complete Spotisaver album page instead of continuing to close the modal and click the download button.
4. The default reload threshold is 5 unsuccessful retries.
5. After a successful reload, the provider verifies that it is still on the expected album page, waits for the real download button to become visible and enabled, and resumes the normal download workflow.
6. The retry counter resets after a successful page reload. If the queue remains full, the same retry and reload cycle can happen again.
7. Only explicit queue rejections count toward this mechanism. Provisional status, unconfirmed states, generic errors, and slow processing must not trigger queue retries or reloads.
8. Existing browser download event monitoring must remain active across reloads so the eventual ZIP download is still captured.
9. Existing command line behaviour and all unrelated provider behaviour remain unchanged.

## Configuration

Add these optional integer settings:

- `queue_retry_interval_seconds`: seconds to wait after an explicit queue rejection before retrying. Default: `25`.
- `queue_reload_after_retries`: number of unsuccessful queue retry attempts after which to reload the album page. Default: `5`.

Example:

```toml
default_provider = "spotisaver"
output_dir = "./output"
show_browser = false
mute_browser_audio = true

# Wait 25 seconds after an explicit queue rejection.
queue_retry_interval_seconds = 25

# Reload the album page after 5 unsuccessful retry attempts.
queue_reload_after_retries = 5
```

Both values must be positive integers. Invalid values must produce actionable configuration errors. Existing config files that omit these keys must continue to work with the new defaults.

## Scope

- Extend TOML configuration parsing, validation, and resolved settings.
- Apply the configurable interval to the Spotisaver queue retry wait.
- Implement the threshold-based full page reload recovery path.
- Preserve strict queue-state validation and browser download event handling.
- Update README configuration documentation and examples.
- Add focused automated tests.

## Acceptance criteria

- A missing config file uses 25 seconds and 5 retries.
- Existing config files without the new keys remain valid.
- User-provided values are applied exactly.
- Invalid, zero, negative, boolean, or non-integer values are rejected with a clear message.
- The normal retry path still closes and verifies the modal before clicking again.
- At the configured threshold, the page is reloaded and the expected album URL and download button are revalidated before continuing.
- The retry counter resets after a successful reload.
- Unconfirmed queue states and generic errors do not increment the queue retry counter.
- Download event monitoring survives the reload and captures the eventual ZIP download.
- The full automated test suite and TKKGData contract smoke test pass.
- No live Spotisaver download is required for automated verification.
