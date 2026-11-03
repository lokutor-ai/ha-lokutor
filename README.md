# Lokutor for Home Assistant

Text-to-speech and speech-to-text from [Lokutor](https://lokutor.com) in Home Assistant, for Assist voice pipelines, automations and `tts.speak`.

- **Text-to-speech** (`tts.lokutor_text_to_speech`): ten voices, nine languages, adjustable speed.
- **Speech-to-text** (`stt.lokutor_speech_to_text`): one model for nine languages, for Assist.

It talks to Lokutor's OpenAI-compatible audio API (`https://api.lokutor.com/v1`). Usage is billed to your Lokutor balance at the [published rates](https://lokutor.com).

## Install

### HACS (custom repository)

1. In HACS, open the menu (top right) and choose **Custom repositories**.
2. Add `https://github.com/lokutor-ai/ha-lokutor` with category **Integration**.
3. Install **Lokutor** and restart Home Assistant.

### Manual

Copy `custom_components/lokutor` into your `config/custom_components` folder and restart.

## Configure

1. Create an API key in the [Lokutor dashboard](https://app.lokutor.com).
2. In Home Assistant: **Settings > Devices & services > Add integration > Lokutor**, and paste the key. The key is checked against the API before the entry is created; if it is later rejected, Home Assistant asks for a new one.
3. **Configure** on the integration sets the default **voice**, **language** and **speed** for text-to-speech.

In **Settings > Voice assistants**, pick Lokutor as the text-to-speech and/or speech-to-text engine.

```yaml
action: tts.speak
target:
  entity_id: tts.lokutor_text_to_speech
data:
  media_player_entity_id: media_player.kitchen
  message: "Dinner is ready."
  language: en
  options:
    voice: M2
    speed: 1.1
```

## Voices

Ten slots, each with a native speaker in every language (the speaker you hear depends on the language too):

| Slot | Name | Slot | Name |
| --- | --- | --- | --- |
| `F1` | Claire | `M1` | James |
| `F2` | Sophie | `M2` | Oliver |
| `F3` | Emma | `M3` | Lucas |
| `F4` | Maria | `M4` | Ethan |
| `F5` | Isabella | `M5` | Noah |

Per-request options: `voice` (a slot above; OpenAI names such as `alloy` and cloned voice ids from your account also work) and `speed` (0.5 to 2.0, default 1.0).

## Languages

English `en`, Spanish `es`, Catalan `ca`, Galician `gl`, Basque `eu`, Portuguese `pt`, French `fr`, Italian `it`, German `de`. Speech and recognition cover all nine. Regional codes such as `es-ES` are accepted.

## Notes

- Audio is always returned as WAV.
- Speech-to-text transcribes a finished utterance (not word-by-word streaming), which is how Assist uses it.
- Developed against API docs at https://docs.lokutor.com/integrations/openai-compatible.

## Development

```bash
uv venv --python 3.13 .venv && uv pip install --python .venv/bin/python -r requirements_test.txt
.venv/bin/python -m pytest          # offline, HTTP mocked
LOKUTOR_API_KEY=... .venv/bin/python scripts/live_smoke.py   # one TTS + one STT call against the real API
```

## License

MIT. Lokutor is a trademark of its owner; this integration is maintained by the Lokutor team.
