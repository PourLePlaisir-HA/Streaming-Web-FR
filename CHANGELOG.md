## 0.8.0-beta.7

- Corrected the SearchBox insertion point in the main Lovelace render.
- SearchBox is now rendered immediately below the debug block and above the first home section.
- Removed accidental SearchBox template insertion from media popup rendering.
- Keeps native Provider search and per-Provider `exact_naming` compatibility.

## 0.8.0-beta.6

- Fixed the SearchBox rendering on the main Lovelace home view.
- The SearchBox is now explicitly displayed below the card header and before the home sections when `searchbox: true`.
- Keeps native Provider search and per-Provider `exact_naming` behavior from the previous betas.

## 0.8.0-beta.5

- Moved the SearchBox to the main Lovelace home view.
- Native Provider search can now be launched directly from the current Streaming Web card without opening the catalog view.
- Search results continue to use the validated Provider search backend and per-Provider `exact_naming` behavior.
- Clearing the SearchBox returns to the normal home sections.

## 0.8.0-beta.4

- Restored the Lovelace SearchBox and connected it to the validated native Provider search backend.
- Added a dedicated WebSocket search command using each Provider's independent search implementation and configuration.
- Search runs only on Enter or the search button, not on every keystroke.
- Minimum query length remains 2 characters and duplicate validated searches are ignored.
- Clearing the SearchBox restores the catalog view.
- Provider-specific `exact_naming` normalization from beta.3 is automatically applied to SearchBox queries.
- Search results reuse the existing poster, details and VLC playback flow.

## 0.8.0-beta.3

- Added per-Provider `exact_naming` search compatibility setting.
- `exact_naming: true` is the default and sends the user query unchanged.
- `exact_naming: false` removes only a recognized leading French elision before the native Provider search (for example `L'Affaire` → `Affaire`).
- Added `exact_naming` to the Provider configuration UI.
- Documented the compatibility behavior and per-Provider scope.
- Keeps the validated native Provider search backend from beta.2.

## 0.8.0-beta.2

- Improved native Provider search request fidelity.
- Prime the Provider session before submitting a search so cookies/context match normal browser navigation.
- Submit search as an URL-encoded form with Origin and Referer headers.
- Keep `streaming_web_fr.search_test` as the validation path for the backend search.
- SearchBox and Lovelace visual-editor configuration are deferred to a later version.

## 0.8.0-beta.1

- Added the first backend implementation of native Provider search.
- Search requests use the Provider's own search form through the configured session and cookie context.
- Added a Home Assistant `streaming_web_fr.search_test` action for diagnostic validation before wiring the Lovelace SearchBox.
- Search results are parsed into the existing `MediaItem` model, preserving the normal details/playback pipeline.
- Minimum search query length is 2 characters.
- SearchBox restoration and its Lovelace UI toggle are intentionally planned for beta.2.

## 0.7.0

- Promoted the validated 0.7 beta cycle to stable.
- Added configurable horizontal/vertical home-section navigation.
- Added bounded vertical scrolling with configurable `poster_rows` (default: `2`) in YAML and the Lovelace visual editor.
- Kept `home_section_count` for home-section availability and `posters_par_lot` for catalog pagination.
- Fixed title parsing for apostrophes such as `L'Affaire Zanetti`, `D'Artagnan` and `Ocean's Eleven`.
- Runtime/debug version is read automatically from `manifest.json`.
- Updated Streaming Web FR visual identity assets.

## 0.7.0-beta.4

- Fixed a regression introduced in beta.3 that could make the home/catalog parser return zero titles.
- Aligned the quote-aware title/alt parser with its named `value` capture.
- Preserves apostrophes inside titles such as `L'Affaire Zanetti`, `D'Artagnan` and `Ocean's Eleven`.
- Includes the cumulative 0.7 beta changes: configurable vertical scrolling, `poster_rows` in YAML and Lovelace UI, automatic runtime version from `manifest.json`, and updated visual identity.
- No intended changes to stream resolution or VLC playback.

## 0.7.0-beta.3

- Fixed Provider title parsing when titles contain apostrophes, including cases such as `L'Affaire`, `D'Artagnan` and `Ocean's Eleven`.
- The parser now closes quoted HTML attributes only with the same quote character that opened them.
- Fixed the Lovelace visual editor so `poster_rows` is actually configurable from the UI.
- Runtime/debug version is now read automatically from `manifest.json` instead of being hardcoded.
- Includes the configurable vertical home scrolling, bounded poster rows and visual identity changes from the 0.7.0 beta cycle.
- No intended changes to Provider playback, stream resolution or VLC launching.

## 0.7.0-beta.2

- Added the validated Streaming Web FR visual identity assets.
- Added configurable home-section direction with `scroll_direction: horizontal|vertical`.
- Added true bounded vertical scrolling for home sections instead of displaying every poster at once.
- Added `poster_rows` to configure the number of visible poster rows in vertical mode; default: `2`.
- Added Lovelace visual editor controls for scroll direction and visible poster rows.
- Kept `home_section_count` as the number of posters available in each home section.
- Kept `posters_par_lot` dedicated to catalog pagination / “Voir N de plus”.
- Kept `horizontal` as the default layout for backward compatibility.
- Provider handling, details, stream resolution and VLC playback are unchanged.

## 0.6.1

- Updated public-facing documentation to use the generic **Provider** wording.
- Kept provider names configurable and displayed dynamically in Lovelace badges.
- Updated the Streaming Web FR integration branding assets.
- No provider parser, routing or playback behavior changes.

## 0.6.0-beta.5

- Added a provider-scoped cookie jar independent from Home Assistant's shared HTTP session.
- Persisted provider cookies across catalog, details, player and manifest requests.
- Replaced automatic redirects with bounded manual redirect handling.
- Applied updated cookies before every redirect, matching browser navigation more closely.
- Added explicit, path-only redirect traces when the provider still returns a loop.
- Kept beta.4 URL and referer validation unchanged.

## 0.6.0-beta.4

- Preserved the source catalog URL for every parsed media item.
- Sent the validated catalog URL as the HTTP referer when opening media details.
- Forwarded the same provider context through details and stream resolution.
- Added a browser-compatible French `Accept-Language` request header.
- Added the source referer to popup diagnostics when `debug: true`.
- Kept the URL validation and redirect-loop safeguards introduced in beta.3.

## 0.6.0-beta.3

- Fixed media details and playback for items loaded from deeper provider catalog pages.
- Preserved and reused the exact provider item URL instead of rebuilding it only from the item ID.
- Added strict same-provider URL validation before a catalog URL can be used by the backend.
- Added canonical trailing-slash and legacy URL fallbacks for provider routing compatibility.
- Added an explicit error when a media page enters a redirect loop.
- Added the media provider ID and page URL to the popup when `debug: true`.
- Kept catalog pagination, search and Android TV / VLC launch behavior unchanged.

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

- Added a Provider-style Lovelace home view with **Derniers ajouts**, **À l'affiche**, **Animations** and **Docs & Spectacles** rails.
- Added **Voir tout** navigation for each home section.
- Added **Explorer le catalogue** and a dedicated catalog view with section filters, search, sorting, provider filter, pagination and optional infinite scroll.
- Extended the Provider parser to detect home sections and follow the provider's **Tout** catalog link.
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
- Includes the Provider provider foundation.
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
- First provider implementation: Provider.
- Generic authentication layer: none, Basic, form login, API key, Bearer, cookie and custom headers.
- Generic provider interface for browse, search, details and stream resolution.
- HLS manifest resolver foundation.
- Multiple Android TV destinations.
- VLC launch via Android Debug Bridge using the validated `ACTION_VIEW` flow.
- Dedicated Lovelace card with provider filtering, search, sorting, responsive posters, popup details, configurable batches and optional infinite scroll.
- No runtime dependency on Streaming Top FR.
