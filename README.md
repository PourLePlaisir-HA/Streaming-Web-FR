# Streaming Web FR

<p align="center">
  <img src="https://raw.githubusercontent.com/PourLePlaisir-HA/Streaming-Web-FR/main/custom_components/streaming_web_fr/brand/icon.png" alt="Streaming Web FR" width="160">
</p>

<p align="center">
  <strong>Configurable web streaming catalogs for Home Assistant, with VLC playback on Android TV.</strong>
</p>

**Streaming Web FR** is an independent Home Assistant integration and Lovelace card for browsing online media catalogs through configurable providers, resolving supported media streams and launching playback in **VLC on Android TV**.

> This repository is fully independent from Streaming Top FR. It shares no runtime, storage, provider or service dependency with that project.

## Current stable release — v0.6.1

The v0.6.1 release is the current validated stable baseline. It introduces the provider home rails and complete catalog navigation, remote pagination/search continuation, strengthened provider session and redirect handling, improved diagnostics, the refreshed Lovelace interface and the updated Streaming Web FR visual identity.

### Functional baseline

- unlimited configurable providers;
- provider priority and enable/disable state;
- pluggable provider architecture;
- generic authentication modes: none, Basic, form login, API key, Bearer token, cookie and custom headers;
- first provider module: Provider;
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

### v0.6.0 highlights

- provider home rails: **Derniers ajouts**, **À l'affiche**, **Animations** and **Docs & Spectacles**;
- **Voir tout** and complete catalog navigation;
- provider-side pagination and catalog search continuation;
- persistent provider cookies and safer redirect handling;
- source URL / referer preservation for media details and playback;
- expanded `debug: true` diagnostics;
- refreshed Lovelace visual design;
- improved provider badges, including the dedicated Provider text styling;
- updated Streaming Web FR project and Home Assistant integration icon.

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
home_section_count: 10
scroll_infini: false
debug: false
```

If `debug` is omitted, it defaults to `false`. Set `debug: true` temporarily for diagnostics. The card can then expose the current view/category, item count, active configuration source, YAML path, detected Android TV destinations and parser issues.

In the catalog view, **Voir N de plus** and optional infinite scroll reveal the local batch first, then transparently request the next page from the provider. Search follows the provider catalog beyond the initially loaded pool. With `debug: true`, the card also shows the integration version, provider page, continuation state and search mode.

The default home view mirrors the provider's editorial structure with horizontal rails for **Derniers ajouts**, **À l'affiche**, **Animations** and **Docs & Spectacles**. **Explorer le catalogue** opens the complete catalog, while **Voir tout** opens the corresponding section.

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
    type: Provider
    enabled: true
    priority: 100
    exact_naming: true
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

### Provider search naming compatibility

`exact_naming` is configured independently for each Provider and defaults to `true` when omitted.

- `exact_naming: true`: the search text is sent unchanged to the Provider. For example, `L'Affaire` is sent as `L'Affaire`.
- `exact_naming: false`: Streaming Web FR removes only a recognized leading French elision before sending the query. For example, `L'Affaire` becomes `Affaire` and `D'Artagnan` becomes `Artagnan`. A title without a leading elision, such as `Matrix`, is unchanged.

This compatibility option is intended for Providers whose native search engine handles apostrophes or leading elisions poorly. It does not globally remove apostrophes from titles or queries.


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

The first implemented provider type is `Provider`. Additional provider modules can be added without changing the Lovelace card or Android TV playback engine.

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


## Home section scrolling (0.7 beta)

The home rails can use the historical horizontal layout or a bounded vertical layout.

```yaml
type: custom:streaming-web-fr-card
scroll_direction: vertical
poster_rows: 2
home_section_count: 20
posters_par_lot: 8
```

- `scroll_direction`: `horizontal` (default) or `vertical`.
- `poster_rows`: visible rows in vertical mode; default `2`.
- `home_section_count`: posters available in each home section.
- `posters_par_lot`: catalog pagination increment used by “Voir N de plus”.
