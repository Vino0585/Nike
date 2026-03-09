import base64
import logging
import requests
import zlib
from pathlib import Path

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

    def preview_zpl_as_image(self, zpl_content, file_name="label_preview.png"):
        """
        Sends ZPL content to the Labelary API to generate a PNG preview.
        Saves the PNG to the Output_files directory.
        """
        if not zpl_content:
            logging.warning("No ZPL content provided for preview.")
            return

        # --- PRE-PROCESSING FOR JAPANESE CHARACTERS ---
        # Check if there are non-ASCII characters and if a ^CI command is missing.
        has_non_ascii = any(ord(c) > 127 for c in zpl_content)
        if has_non_ascii and "^CI" not in zpl_content.upper():
            logging.warning("Non-ASCII characters detected. Injecting ^CI28 for Japanese character support.")
            # Inject ^CI28 after the first ^XA (start of label)
            if zpl_content.strip().startswith("^XA"):
                zpl_content = zpl_content.replace("^XA", "^XA^CI28", 1)
            else:
                # If no ^XA is found at the start, add it.
                zpl_content = "^XA^CI28" + zpl_content
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
