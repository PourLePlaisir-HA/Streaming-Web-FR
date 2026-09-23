# Changelog

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