# Changelog

## 0.5.0

First stable release.

- Promotes the validated multi-provider architecture to stable.
- Uses `/config/streaming_web_fr.yaml` as the canonical configuration source when present.
- Supports unlimited providers and Android TV destinations.
- Includes extensible provider authentication modes.
- Includes the Drabam provider foundation.
- Includes Android TV / VLC playback via Android Debug Bridge.
- Adds `streaming_web_fr.reload_config` for YAML reload without Home Assistant restart.
- Includes responsive Lovelace browsing, search, filtering, sorting, pagination and optional infinite scroll.
- Includes runtime player synchronization and optional card diagnostics.
- YAML parser accepts both list and ID-keyed mapping syntax.
- Invalid provider/player blocks are exposed through diagnostics instead of being silently discarded.
- Validated on the current Home Assistant test environment.

## 0.1.0-beta.4

Player discovery and diagnostics hotfix.

- Resynchronizes Android TV destinations from the backend every time a media popup opens.
- Adds a manual refresh button to the Lovelace card.
- Adds optional `debug: true` card diagnostics.
- Shows active configuration source, YAML path, detected player count/IDs and parser issues.
- YAML parser now accepts both list syntax and ID-keyed mapping syntax for providers and players.
- Invalid provider/player blocks are no longer silently discarded: parser issues are exposed to the card.
- Adds runtime configuration diagnostics over the internal WebSocket API.
- Removes the redundant Config Entry update listener from the dev branch.

## 0.1.0-beta.3

YAML configuration foundation.

- Adds `/config/streaming_web_fr.yaml` as the canonical configuration source when present.
- Adds a public anonymized template: `streaming_web_fr.example.yaml`.
- Supports unlimited providers and Android TV destinations from YAML.
- Keeps provider authentication data in YAML, including none, Basic, form login, API key, Bearer, cookie and custom headers.
- Adds the Home Assistant action `streaming_web_fr.reload_config` to reload YAML without restarting Home Assistant.
- Keeps Config Entry / Options Flow as a temporary fallback when the YAML file is absent.
- The future configuration UI will be built on top of this same configuration model.

## 0.1.0-beta.2

Configuration hotfix.

- Fixes an `Unknown error occurred` when saving an Android TV destination from the Home Assistant Options Flow.
- Removes the redundant integration update listener because `OptionsFlowWithReload` already reloads the Config Entry.
- Initializes provider/player edit-flow state explicitly.
- No change to provider catalog parsing, HLS resolution or VLC launch logic.

## 0.1.0-beta.1

Initial architecture beta.

- New independent Home Assistant integration: `streaming_web_fr`.
- Unlimited provider list stored in the Config Entry.
- First provider implementation: Drabam.
- Generic authentication layer: none, Basic, form login, API key, Bearer, cookie and custom headers.
- Generic provider interface for browse, search, details and stream resolution.
- HLS manifest resolver foundation.
- Multiple Android TV destinations.
- VLC launch via Android Debug Bridge using the validated `ACTION_VIEW` flow.
- Dedicated Lovelace card with provider filtering, search, sorting, responsive posters, popup details, configurable batches and optional infinite scroll.
- No runtime dependency on Streaming Top FR.