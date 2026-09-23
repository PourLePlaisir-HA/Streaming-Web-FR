# Streaming Web FR

<p align="center">
  <img src="icon.svg" alt="Streaming Web FR" width="160">
</p>

<p align="center">
  <strong>Configurable web streaming catalogs for Home Assistant, with VLC playback on Android TV.</strong>
</p>

**Streaming Web FR** is an independent Home Assistant integration and Lovelace card for browsing online media catalogs through configurable providers, resolving supported media streams and launching playback in **VLC on Android TV**.

> This repository is fully independent from Streaming Top FR. It shares no runtime, storage, provider or service dependency with that project.

## Current stable baseline — v0.5.0

The v0.5.0 codebase provides:

- unlimited configurable providers;
- provider priority and enable/disable state;
- pluggable provider architecture;
- generic authentication modes: none, Basic, form login, API key, Bearer token, cookie and custom headers;
- first provider module: Drabam;
- normalized catalog model shared by all providers;
- provider aggregation;
- HLS resolver foundation;
- multiple Android TV destinations;
- VLC launch through Home Assistant Android Debug Bridge;
- Lovelace card with provider filter, search, sorting, responsive posters and details popup;
- configurable **Voir N de plus** pagination;
- optional infinite scroll;
- runtime YAML reload;
- diagnostics mode.

## Installation

1. Add this repository to HACS as a custom **Integration** repository.
2. Install **Streaming Web FR**.
3. Restart Home Assistant.
4. Add the integration from **Settings → Devices & Services**.

The Lovelace resource is registered automatically by the integration.

## Lovelace

Minimal configuration:

```yaml
type: custom:streaming-web-fr-card
title: Streaming Web
```

Extended example:

```yaml
type: custom:streaming-web-fr-card
title: Streaming Web
searchbox: true
posters_par_lot: 8
scroll_infini: false
debug: false
```

Set `debug: true` temporarily for diagnostics. The card can then expose the active configuration source, YAML path, detected Android TV destinations and parser issues.

## YAML configuration

When present, **`/config/streaming_web_fr.yaml` is the canonical configuration source**.

A complete public template is provided as:

```text
streaming_web_fr.example.yaml
```

Example:

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

If `/config/streaming_web_fr.yaml` does not exist, the integration falls back to the Config Entry / Options Flow configuration for backward compatibility.

## Providers

The provider layer is modular. Each provider can define its own:

- ID and display name;
- provider type;
- base URL;
- priority;
- enabled/disabled state;
- authentication mode.

The first implemented provider type is `drabam`. Additional provider modules can be added without changing the Lovelace card or Android TV playback engine.

## Android TV / VLC

A destination uses generic Home Assistant entities, for example:

```yaml
id: androidtv1
name: AndroidTV1
media_player: media_player.androidtv1
remote: remote.androidtv1
adb_player: media_player.androidtv1_adb
```

Playback flow:

```text
Home Assistant
→ Android Debug Bridge
→ Android ACTION_VIEW
→ VLC
→ resolved media URL
```

## Security

Streaming Web FR does not ship media, provider credentials, DRM bypassing code or a hosted catalog.

Credentials remain local to your Home Assistant installation. If you store credentials in `streaming_web_fr.yaml`, keep that file private and never commit it to a public repository.

Use providers and content only where you are authorized to access them.

## Project identity

The project icon combines a geometric cloud, a discreet play symbol and streaming waves in **turquoise + anthracite**, deliberately avoiding YouTube-like visual codes.

## License

MIT
