import streamlit as st
import json
from Payload_generation.ASN_Creation_Payload import Asn_Payload_Generator

st.set_page_config(layout="wide", page_title="ASN Payload Generator")

st.title("🤖 ASN Payload Generation Bot")
st.markdown("""
Welcome! This tool allows you to generate ASN payloads interactively.
1.  **Upload** your ASN creation Excel file below.
2.  **Click** the 'Generate Payloads' button.
3.  **Review** and **copy** the generated JSON payloads that appear.
""")

# --- File Uploader ---
uploaded_file = st.file_uploader(
    "Choose your ASN Creation Excel file",
    type=['xlsx', 'xls']
)

if uploaded_file is not None:
    st.success(f"File '{uploaded_file.name}' uploaded successfully!")

    # --- Generation Button ---
    if st.button("🚀 Generate Payloads", type="primary", use_container_width=True):
        with st.spinner('Generating payloads... Please wait.'):
            try:
                # Instantiate the generator with the uploaded file's buffer
                asn_generator = Asn_Payload_Generator(excel_file_buffer=uploaded_file)
                final_payloads = asn_generator.generate_payloads

                if final_payloads:
                    st.success(f"✅ Generation Complete! {len(final_payloads)} payloads created.")
                    # --- Display Payloads ---
                    for i, payload_data in enumerate(final_payloads):
                        env = payload_data.get('environment', 'N/A')
                        asn_id = payload_data.get('payload', {}).get('AsnId', 'N/A')
                        with st.expander(f"Payload #{i + 1}  |  Environment: {env}  |  ASN ID: {asn_id}"):
                            st.json(payload_data['payload'])
                else:
                    st.warning(
                        "Generation finished, but no payloads were created. Please check your input file for valid data.")
            except Exception as e:
                st.error(f"An unexpected error occurred during payload generation.")
                st.exception(e)  # This will print the full traceback for debugging