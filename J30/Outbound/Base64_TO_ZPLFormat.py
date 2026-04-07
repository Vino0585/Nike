import base64
import logging
import requests
import zlib
from pathlib import Path

try:
    from google.cloud import translate_v2
    GOOGLE_TRANSLATE_AVAILABLE = True
except ImportError:
    translate_v2 = None
    GOOGLE_TRANSLATE_AVAILABLE = False
    logging.warning("google-cloud-translate not installed. Falling back to character removal.")

# Setup basic logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

class Base64ToZPL:
    """Utility class to handle Base64 to ZPL conversions."""

    def decode_base64_to_zpl(self, b64_string):
        """Decodes a base64 string (handling potential compression) and returns the ZPL string."""
        try:
            # 1. Decode Base64 to bytes
            decoded_bytes = base64.b64decode(b64_string)
            
            # 2. Attempt to decompress (GZIP/ZLIB)
            try:
                # 16 + zlib.MAX_WBITS triggers automatic header detection for gzip/zlib
                decompressed_bytes = zlib.decompress(decoded_bytes, 16 + zlib.MAX_WBITS)
                logging.info("Detected compressed data. Successfully decompressed.")
                decoded_bytes = decompressed_bytes
            except zlib.error:
                # Not compressed or unknown compression; proceed with original bytes
                pass

            # 3. Decode bytes to string
            # Try UTF-8 first (standard for modern ZPL)
            try:
                return decoded_bytes.decode("utf-8")
            except UnicodeDecodeError:
                logging.info("UTF-8 decode failed. Retrying with Shift-JIS.")
                # Fallback to Shift-JIS (common for Japanese legacy ZPL)
                return decoded_bytes.decode("shift_jis", errors="replace")

        except Exception as e:
            logging.error(f"Failed to process Base64 string: {e}")
            return None

    def save_zpl_to_file(self, zpl_content, file_name="label_output.zpl"):
        """Saves the decoded ZPL content to the Output_files directory."""
        if not zpl_content:
            logging.warning("No ZPL content provided to save.")
            return

        try:
            output_dir = Path("../Output_files")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_filepath = output_dir / file_name

            with open(output_filepath, "w", encoding="utf-8") as f:
                f.write(zpl_content)
            
            logging.info(f"Successfully saved ZPL to: {output_filepath}")
        except Exception as e:
            logging.error(f"An error occurred while saving ZPL file: {e}")

    def _translate_japanese_to_english(self, text):
        """
        Translates Japanese text to English using Google Cloud Translate API.
        Falls back to character removal if Google Translate is not available.

        Args:
            text: The text containing Japanese characters to translate

        Returns:
            Text with Japanese characters translated to English
        """
        if not GOOGLE_TRANSLATE_AVAILABLE or translate_v2 is None:
            logging.warning("Google Translate not available. Removing Japanese characters instead.")
            return self._remove_japanese_characters(text)

        try:
            translate_client = translate_v2.Client()

            # Extract only non-ASCII parts for translation (preserve ZPL commands)
            import re

            # Find all text segments that contain Japanese characters
            # ZPL format: ^FD[text]^FS, so we'll extract and translate text content
            def translate_segment(match):
                segment = match.group(0)
                if any(ord(c) > 127 for c in segment):
                    try:
                        result = translate_client.translate_text(
                            segment,
                            source_language='ja',
                            target_language='en'
                        )
                        translated = result['translatedText']
                        logging.info(f"Translated '{segment}' -> '{translated}'")
                        return translated
                    except Exception as e:
                        logging.warning(f"Translation failed for '{segment}': {e}. Removing instead.")
                        return self._remove_japanese_characters(segment)
                return segment

            # Pattern to match text between ZPL control sequences
            # This captures text content while preserving ZPL commands
            pattern = r'(?<=\^FD)[^^]*(?=\^FS)'
            translated_text = re.sub(pattern, translate_segment, text)

            return translated_text

        except Exception as e:
            logging.error(f"Translation error: {e}. Falling back to character removal.")
            return self._remove_japanese_characters(text)

    def _remove_japanese_characters(self, text):
        """
        Removes Japanese characters (Hiragana, Katakana, Kanji, and common symbols)
        while preserving ASCII and other characters.
        """
        filtered_chars = []
        for char in text:
            code_point = ord(char)
            # Check if character is in Japanese ranges
            if not ((0x3040 <= code_point <= 0x309F) or  # Hiragana
                    (0x30A0 <= code_point <= 0x30FF) or  # Katakana
                    (0x4E00 <= code_point <= 0x9FFF) or  # Kanji
                    (0xF900 <= code_point <= 0xFAFF)):   # CJK Compatibility
                filtered_chars.append(char)

        return ''.join(filtered_chars)

    def preview_zpl_as_image(self, zpl_content, file_name="label_preview.png", translate_japanese=True):
        """
        Sends ZPL content to the Labelary API to generate a PNG preview.
        Saves the PNG to the Output_files directory.

        Args:
            zpl_content: The ZPL content to preview
            file_name: Output filename for the preview image
            translate_japanese: If True, translates Japanese to English. If False, removes Japanese characters.
        """
        if not zpl_content:
            logging.warning("No ZPL content provided for preview.")
            return

        # --- PRE-PROCESSING FOR JAPANESE CHARACTERS ---
        has_non_ascii = any(ord(c) > 127 for c in zpl_content)

        if has_non_ascii:
            if translate_japanese:
                logging.warning("Japanese/non-ASCII characters detected. Attempting translation to English.")
                zpl_content = self._translate_japanese_to_english(zpl_content)
            else:
                logging.warning("Japanese/non-ASCII characters detected. Removing them.")
                zpl_content = self._remove_japanese_characters(zpl_content)
        # --- END PRE-PROCESSING ---

        try:
            # Adjust density (dpmm) and dimensions (width x height in inches) as needed
            # 8dpmm is approx 203dpi. 4x8 inches is the label size.
            url = 'http://api.labelary.com/v1/printers/8dpmm/labels/4x8/0/'
            
            headers = {'Accept': 'image/png'}
            
            # Labelary expects the ZPL in the body.
            # We encode back to UTF-8 for transmission.
            response = requests.post(url, headers=headers, data=zpl_content.encode("utf-8"), stream=True)
            
            if response.status_code == 200:
                output_dir = Path("../Output_files")
                output_dir.mkdir(parents=True, exist_ok=True)
                output_filepath = output_dir / file_name
                
                with open(output_filepath, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                
                logging.info(f"Successfully saved label preview to: {output_filepath}")
            else:
                logging.error(f"Labelary API returned error: {response.status_code} - {response.text}")

        except Exception as e:
            logging.error(f"An error occurred while generating label preview: {e}")

if __name__ == '__main__':
    # Sample Base64 string provided by the user
    b64_input = input("Paste your Base64 string here: ")
    
    converter = Base64ToZPL()
    zpl_output = converter.decode_base64_to_zpl(b64_input)
    
    if zpl_output:
        print("\n--- Decoded ZPL Content ---")
        print(zpl_output)
        print("---------------------------\n")
        
        # Save ZPL text file
        converter.save_zpl_to_file(zpl_output)
        
        # Generate and save PNG preview
        converter.preview_zpl_as_image(zpl_output)