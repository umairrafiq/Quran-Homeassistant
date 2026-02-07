# Quran Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/umairrafiq/Quran-Homeassistant.svg)](https://github.com/umairrafiq/Quran-Homeassistant/releases)
[![License](https://img.shields.io/github/license/umairrafiq/Quran-Homeassistant.svg)](LICENSE)

A Home Assistant integration for the Holy Quran, powered by [AlQuran.cloud API](https://alquran.cloud/api).

## Features

- 🎙️ **Play Quran Audio** - Play any Surah or Ayah on your media players
- 📖 **Daily Ayah Sensor** - Get a new ayah every day with Arabic text and translation
- 🕌 **Multiple Reciters** - Choose from famous reciters like Al-Afasy, Abdul Basit, As-Sudais
- 🌍 **Multiple Translations** - English, Urdu, French, German, Turkish, and more
- ⚡ **Service Calls** - Automate Quran recitation with Home Assistant automations

## Installation

### HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=umairrafiq&repository=Quran-Homeassistant&category=integration)

**Or manually:**

1. Open HACS in Home Assistant
2. Click on **Integrations**
3. Click the **⋮** menu (top right) → **Custom repositories**
4. Add repository URL: `https://github.com/umairrafiq/Quran-Homeassistant`
5. Select category: **Integration**
6. Click **Add**
7. Search for "Quran" and click **Download**
8. Restart Home Assistant

### Manual Installation

1. Download the [latest release](https://github.com/umairrafiq/Quran-Homeassistant/releases)
2. Extract and copy `custom_components/quran` to your `config/custom_components/` directory
3. Restart Home Assistant

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for "Quran"
3. Select your preferred reciter and translation
4. Click Submit

## Sensors

| Sensor | Description |
|--------|-------------|
| `sensor.quran_daily_ayah` | Today's ayah (translation) |
| `sensor.quran_daily_ayah_arabic` | Today's ayah (Arabic text) |
| `sensor.quran_daily_ayah_audio` | Audio URL for today's ayah |

### Sensor Attributes

The daily ayah sensor includes these attributes:
- `ayah_number` - Absolute ayah number (1-6236)
- `surah_number` - Surah number (1-114)
- `surah_name` - Surah name in English
- `reference` - Reference like "2:255"
- `full_text` - Complete ayah text
- `audio_url` - Direct MP3 link

## Services

### `quran.play_surah`

Play a complete Surah on a media player.

```yaml
service: quran.play_surah
data:
  surah: 55  # Surah Ar-Rahman
  media_player: media_player.living_room
  reciter: ar.alafasy  # Optional
```

### `quran.play_ayah`

Play a specific ayah.

```yaml
service: quran.play_ayah
data:
  ayah: 262  # Ayat ul Kursi (2:255)
  media_player: media_player.bedroom
```

### `quran.play_ayat_ul_kursi`

Quick shortcut to play Ayat ul Kursi.

```yaml
service: quran.play_ayat_ul_kursi
data:
  media_player: media_player.bedroom
```

## Automation Examples

### Play Surah Al-Kahf on Friday

```yaml
automation:
  - alias: "Play Surah Al-Kahf on Friday"
    trigger:
      - platform: time
        at: "09:00:00"
    condition:
      - condition: time
        weekday:
          - fri
    action:
      - service: quran.play_surah
        data:
          surah: 18
          media_player: media_player.living_room
```

### Play Ayat ul Kursi After Fajr

```yaml
automation:
  - alias: "Ayat ul Kursi after Fajr"
    trigger:
      - platform: state
        entity_id: sensor.islamic_prayer_times_fajr_prayer
    action:
      - delay: "00:05:00"
      - service: quran.play_ayat_ul_kursi
        data:
          media_player: media_player.bedroom
```

### Morning Adhkar with Daily Ayah

```yaml
automation:
  - alias: "Morning Quran"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: media_player.play_media
        target:
          entity_id: media_player.kitchen
        data:
          media_content_type: music
          media_content_id: "{{ state_attr('sensor.quran_daily_ayah_audio', 'audio_url') }}"
```

### Display Daily Ayah on Dashboard

```yaml
type: markdown
content: |
  ## 📖 Ayah of the Day
  
  **{{ state_attr('sensor.quran_daily_ayah', 'surah_name') }}** 
  ({{ state_attr('sensor.quran_daily_ayah', 'reference') }})
  
  > {{ state_attr('sensor.quran_daily_ayah', 'full_text') }}
  
  ---
  {{ states('sensor.quran_daily_ayah_arabic') }}
```

## Example Dashboard

### Step 1: Create a Script (Required for Play Button)

Go to **Settings → Automations & Scenes → Scripts → Create Script** and add:

```yaml
alias: Play Daily Ayah
icon: mdi:book-open-page-variant
description: Play today's Quran ayah with Arabic recitation and translation
sequence:
  # Announce surah name
  - action: tts.speak
    target:
      entity_id: tts.piper  # Change to your TTS entity
    data:
      cache: true
      media_player_entity_id: media_player.living_room  # Change this!
      message: >-
        Ayah of the day from Surah {{ state_attr('sensor.quran_daily_ayah', 'surah_name') }}, 
        verse {{ state_attr('sensor.quran_daily_ayah', 'ayah_in_surah') }}
  - delay:
      seconds: 4
  # Play Arabic recitation
  - action: media_player.play_media
    target:
      entity_id: media_player.living_room  # Change this!
    data:
      media_content_type: music
      media_content_id: "{{ states('sensor.quran_daily_ayah_audio') }}"
  - delay:
      seconds: 15
  # Speak translation
  - action: tts.speak
    target:
      entity_id: tts.piper  # Change to your TTS entity
    data:
      cache: true
      media_player_entity_id: media_player.living_room  # Change this!
      message: "{{ state_attr('sensor.quran_daily_ayah', 'full_text') }}"
mode: single
```

> 💡 **No TTS?** See [`examples/scripts.yaml`](examples/scripts.yaml) for a simple audio-only version.

### Step 2: Add Dashboard Card

Go to your dashboard → **Edit** → **Add Card** → **Manual** → Paste:

```yaml
type: vertical-stack
cards:
  - type: markdown
    title: 📖 Ayah of the Day
    content: |
      **{{ state_attr('sensor.quran_daily_ayah', 'surah_name') }}** 
      {{ state_attr('sensor.quran_daily_ayah', 'reference') }}
      
      <p style="font-size: 1.5em; text-align: right; direction: rtl; line-height: 1.8;">
      {{ states('sensor.quran_daily_ayah_arabic') }}
      </p>
      
      ---
      > {{ state_attr('sensor.quran_daily_ayah', 'full_text') }}

  - type: button
    name: ▶️ Play Daily Ayah
    icon: mdi:play-circle
    icon_height: 50px
    tap_action:
      action: call-service
      service: script.play_daily_ayah

  - type: horizontal-stack
    cards:
      - type: button
        name: Ayat ul Kursi
        icon: mdi:shield-cross
        tap_action:
          action: call-service
          service: quran.play_ayat_ul_kursi
          data:
            media_player: media_player.living_room

      - type: button
        name: Al-Fatiha
        icon: mdi:book-open-variant
        tap_action:
          action: call-service
          service: quran.play_surah
          data:
            surah: 1
            media_player: media_player.living_room

      - type: button
        name: Ar-Rahman
        icon: mdi:heart
        tap_action:
          action: call-service
          service: quran.play_surah
          data:
            surah: 55
            media_player: media_player.living_room

      - type: button
        name: Yasin
        icon: mdi:alpha-y-circle
        tap_action:
          action: call-service
          service: quran.play_surah
          data:
            surah: 36
            media_player: media_player.living_room
```

> ⚠️ **Important:** Replace `media_player.living_room` with your actual media player entity ID!

See [`examples/`](examples/) folder for:
- [`scripts.yaml`](examples/scripts.yaml) - Helper scripts
- [`dashboard.yaml`](examples/dashboard.yaml) - Full dashboard with surah selector
- [`simple-card.yaml`](examples/simple-card.yaml) - Minimal card example

## Available Reciters

| Identifier | Reciter |
|------------|---------|
| `ar.alafasy` | Mishary Rashid Al-Afasy |
| `ar.abdulbasitmurattal` | Abdul Basit (Murattal) |
| `ar.abdurrahmaansudais` | Abdurrahman As-Sudais |
| `ar.minshawi` | Mohamed Siddiq Al-Minshawi |
| `ar.husary` | Mahmoud Khalil Al-Husary |
| `ar.abdulsamad` | Abdul Samad |
| `ar.shaatree` | Abu Bakr Ash-Shaatree |

## Available Translations

| Identifier | Translation |
|------------|-------------|
| `en.asad` | Muhammad Asad (English) |
| `en.sahih` | Saheeh International (English) |
| `en.yusufali` | Yusuf Ali (English) |
| `ur.jalandhry` | Fateh Muhammad Jalandhry (Urdu) |
| `fr.hamidullah` | Hamidullah (French) |
| `de.bubenheim` | Bubenheim & Elyas (German) |

## API

This integration uses the free [AlQuran.cloud API](https://alquran.cloud/api).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [AlQuran.cloud](https://alquran.cloud) for providing the free API
- The Home Assistant community
