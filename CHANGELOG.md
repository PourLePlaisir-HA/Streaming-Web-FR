# Changelog

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
