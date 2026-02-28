import base64
import logging
import requests
from pathlib import Path

# Setup basic logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

class Base64ToZPL:
    """Utility class to handle Base64 to ZPL conversions."""

    def decode_base64_to_zpl(self, b64_string):
        """Decodes a base64 string and returns the ZPL string."""
        try:
            # Decode base64 bytes to bytes, then decode bytes to string
            zpl_data = base64.b64decode(b64_string).decode("utf-8", errors="replace")
            return zpl_data
        except Exception as e:
            logging.error(f"Failed to decode Base64 string: {e}")
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

        try:
            # Adjust density (dpmm) and dimensions (width x height in inches) as needed
            # 8dpmm is approx 203dpi. 4x8 inches is standard shipping label size.
            url = 'http://api.labelary.com/v1/printers/8dpmm/labels/4x8/0/'
            
            headers = {'Accept': 'image/png'}
            
            # Labelary expects the ZPL in the body
            response = requests.post(url, headers=headers, data=zpl_content, stream=True)
            
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
