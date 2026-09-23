## 0.6.0-beta.2

- Added real provider-side catalog pagination with opaque continuation cursors.
- **Voir N de plus** now fetches the next provider page after the local pool is exhausted.
- Infinite scroll now extends the remote catalog instead of stopping at the initial fetch.
- Added bounded global catalog search with continuation when no native provider search is available.
- Added duplicate-page and empty-page guards to stop pagination safely.
- Added multi-provider cursor support without exposing provider pagination details to Lovelace.
- Added integration version, provider page, `has_more`, cursor and search mode to `debug: true`.
- Kept `debug: false` as the implicit default.
- Kept the home rails, media popup and Android TV / VLC playback unchanged.

## 0.6.0-beta.1

- Added a Drabam-style Lovelace home view with **Derniers ajouts**, **À l'affiche**, **Animations** and **Docs & Spectacles** rails.
- Added **Voir tout** navigation for each home section.
- Added **Explorer le catalogue** and a dedicated catalog view with section filters, search, sorting, provider filter, pagination and optional infinite scroll.
- Extended the Drabam parser to detect home sections and follow the provider's **Tout** catalog link.
- Kept Android TV / VLC playback and the existing details popup unchanged.
- Kept user-state features out of this project: no **Ma liste**, **Vu** or **Pas encore vu** UI.
- Added `home_section_count` (default: `10`) for the number of posters displayed per home rail.
- Confirmed Lovelace `debug` defaults to `false` when omitted; `debug: true` exposes technical view/category, item count, config source, players and parser/config issues.

# Changelog

## 0.5.1

Stable documentation and branding release.

- Keeps the validated v0.5.0 runtime and playback behavior unchanged.
- Adds the completed public README.
- Documents installation, Lovelace configuration, YAML configuration and Android TV / VLC playback.
- Adds the Streaming Web FR project icon.
- Introduces the turquoise + anthracite project identity.
- Bumps the integration manifest and VERSION file to 0.5.1.

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
