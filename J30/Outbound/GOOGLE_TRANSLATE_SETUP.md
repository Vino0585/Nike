# Google Translate Setup for ZPL Japanese to English Translation

## Overview
The `Base64ToZPL` class now supports translating Japanese characters to English in ZPL labels before sending to the Labelary API.

## Features
- **Option 1: Google Cloud Translation** - Translates Japanese to English using Google's Neural Machine Translation
- **Option 2: Character Removal** - Falls back to removing Japanese characters if Google Translate is unavailable

## Setup Instructions

### Step 1: Install google-cloud-translate package
```bash
pip install google-cloud-translate
```

### Step 2: Set up Google Cloud Credentials
You need a Google Cloud Project with the Translation API enabled:

#### Option A: Using Service Account JSON (Recommended for CI/CD)
1. Create a service account in Google Cloud Console
2. Download the JSON key file
3. Set the environment variable:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"
   ```

#### Option B: Using Application Default Credentials (Local Development)
1. Install Google Cloud SDK: https://cloud.google.com/sdk/docs/install
2. Authenticate:
   ```bash
   gcloud auth application-default login
   ```

### Step 3: Verify Installation
```python
from google.cloud import translate_v2

# Test translation
translate_client = translate_v2.Client()
result = translate_client.translate_text(
    "こんにちは",
    source_language="ja",
    target_language="en"
)
print(result['translatedText'])  # Should print "Hello"
```

## Usage

### Automatic Translation (Default)
```python
from Outbound.Base64_TO_ZPLFormat import Base64ToZPL

converter = Base64ToZPL()
zpl_with_japanese = "^XA^FDサンプル^FS^XZ"

# This will automatically translate Japanese to English
converter.preview_zpl_as_image(zpl_with_japanese)
# Equivalent to: preview_zpl_as_image(zpl_with_japanese, translate_japanese=True)
```

### Remove Japanese Characters (Fallback)
```python
# If you want to remove instead of translate:
converter.preview_zpl_as_image(zpl_with_japanese, translate_japanese=False)
```

### Full Workflow
```python
from Outbound.Base64_TO_ZPLFormat import Base64ToZPL

converter = Base64ToZPL()

# Decode Base64 to ZPL
b64_input = "..."  # Your base64 encoded ZPL
zpl_output = converter.decode_base64_to_zpl(b64_input)

# Save ZPL file
converter.save_zpl_to_file(zpl_output)

# Generate preview (with Japanese translation)
converter.preview_zpl_as_image(zpl_output, translate_japanese=True)
```

## Behavior

| Scenario | Behavior |
|----------|----------|
| Google Translate installed & credentials valid | Translates Japanese text to English |
| Google Translate not installed | Falls back to removing Japanese characters |
| Translation API fails | Falls back to removing Japanese characters |
| No Japanese characters detected | ZPL sent as-is to Labelary |

## Supported Languages
Japanese (ja) → English (en)

For other languages, modify the `_translate_japanese_to_english()` method:
```python
result = translate_client.translate_text(
    segment,
    source_language='fr',  # French
    target_language='en'
)
```

## Troubleshooting

### "google-cloud-translate not installed"
```bash
pip install google-cloud-translate
```

### "Credentials not found"
Ensure `GOOGLE_APPLICATION_CREDENTIALS` is set:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
python your_script.py
```

### Translation API quota exceeded
- Check your Google Cloud Console quota limits
- Consider batching translations
- Use character removal mode instead

## Costs
Google Cloud Translation is a paid service. Check pricing at:
https://cloud.google.com/translate/pricing

Free tier: 500,000 characters/month

