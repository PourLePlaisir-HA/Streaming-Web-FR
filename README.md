# Streaming Web FR

**Streaming Web FR** is an independent Home Assistant integration and Lovelace card for browsing online media catalogs through configurable providers and launching resolved media streams in VLC on Android TV.

> This repository is fully independent from Streaming Top FR. It shares no runtime, storage, provider, or service dependency with that project.

## v0.1.0-beta.1

First architecture beta:

- unlimited configurable providers;
- provider priority and enable/disable state;
- pluggable provider architecture;
- generic authentication modes: none, Basic, API key, Bearer token, cookie, custom headers;
- first provider module: Drabam;
- normalized catalog model shared by all providers;
- provider aggregation;
- HLS resolver foundation;
- Android TV destinations managed independently;
- VLC launch through Home Assistant Android Debug Bridge;
- Lovelace card with provider filter, search, sorting, responsive posters, details popup, **Voir plus**, configurable batch size and optional infinite scroll.

## Lovelace

```yaml
type: custom:streaming-web-fr-card
title: Streaming Web
searchbox: true
posters_par_lot: 8
scroll_infini: false
```

The card resource is registered automatically by the integration.

## Providers

Providers are configured from:

**Settings → Devices & Services → Streaming Web FR → Configure**

The architecture does not impose a fixed number of providers. Each provider has its own ID, display name, base URL, authentication data and priority.

The initial provider type is `drabam`. Additional provider modules can be added without changing the Lovelace card or playback engine.

## Android TV / VLC

A destination contains generic Home Assistant entities:

```text
Name: AndroidTV1
Remote: remote.androidtv1
ADB media player: media_player.androidtv1_adb
```

Resolved HLS URLs are sent to VLC using an Android `ACTION_VIEW` intent.

## Security

Credentials stay in the Home Assistant Config Entry and are never sent to the Lovelace card. The frontend receives only non-secret provider metadata.

Streaming Web FR does not ship media, provider credentials, DRM bypassing code, or a hosted catalog. Use providers and content only where you are authorized to access them.

## License

MIT
