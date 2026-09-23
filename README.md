# Streaming Web FR

**Streaming Web FR** is an independent Home Assistant integration and Lovelace card for browsing online media catalogs through configurable providers and launching resolved media streams in VLC on Android TV.

> This repository is fully independent from Streaming Top FR. It shares no runtime, storage, provider, or service dependency with that project.

## v0.1.0-beta.3

First architecture beta:

- unlimited configurable providers;
- provider priority and enable/disable state;
- pluggable provider architecture;
- generic authentication modes: none, Basic, form login, API key, Bearer token, cookie, custom headers;
- first provider module: Drabam;
- normalized catalog model shared by all providers;
- provider aggregation;
- HLS resolver foundation;
- Android TV destinations managed independently;
- VLC launch through Home Assistant Android Debug Bridge;
- Lovelace card with provider filter, search, sorting, responsive posters, details popup, **Voir plus**, configurable batch size and optional infinite scroll.

## Installation

Add this repository to HACS as a custom **Integration** repository, install **Streaming Web FR**, restart Home Assistant, then add the integration from **Settings → Devices & Services**.

For the first Drabam provider, the configurable base URL is the provider entry point (for example the current access prefix, not a hard-coded value in the integration).

## Lovelace

```yaml
type: custom:streaming-web-fr-card
title: Streaming Web
searchbox: true
posters_par_lot: 8
scroll_infini: false
```

The card resource is registered automatically by the integration.

## Configuration

When present, **`/config/streaming_web_fr.yaml` is the canonical configuration source**.

A complete public template is provided in the repository as:

`streaming_web_fr.example.yaml`

Typical structure:

```yaml
version: 1

providers:
  - id: provider_main
    name: Provider principal
    type: drabam
    enabled: true
    priority: 100
    base_url: https://example.com/access-prefix
    auth:
      mode: none

players:
  - id: androidtv1
    name: AndroidTV1
    type: android_tv
    media_player: media_player.androidtv1
    remote: remote.androidtv1
    adb_player: media_player.androidtv1_adb
```

The number of providers and Android TV destinations is not limited.

After editing the YAML file, reload it from **Developer Tools → Actions** with:

```text
streaming_web_fr.reload_config
```

A full Home Assistant restart is not required.

If the YAML file does not exist, the integration temporarily falls back to the Config Entry / Options Flow configuration for backward compatibility.

The first implemented provider type is `drabam`. Additional provider modules can be added without changing the Lovelace card or playback engine.

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