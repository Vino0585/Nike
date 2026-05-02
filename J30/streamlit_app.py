import streamlit as st

from Outbound.MHE_Journal_Outbound_Copy import MHEJournalOutboundCopy


st.set_page_config(page_title="MHE Journal Outbound", page_icon="📦", layout="wide")
st.title("MHE Journal Outbound by Wave")
st.write("Enter wave information, run the outbound journal, and download the Excel result.")

with st.form("wave_form"):
    wave_number = st.text_input("Wave Number", placeholder="Example: 12345678")
    environment = st.selectbox("Environment", options=["qa", "prod", "dev"], index=0)
    plant_id = st.text_input("Plant", value="1081")
    submitted = st.form_submit_button("Run MHE Journal")

if submitted:
    if not wave_number.strip():
        st.error("Wave Number is required.")
    elif not plant_id.strip():
        st.error("Plant is required.")
    else:
        with st.spinner("Running outbound MHE journal calls..."):
            try:
                runner = MHEJournalOutboundCopy()
                result = runner.run_for_wave(
                    wave_number=wave_number.strip(),
                    environment=environment.strip(),
                    plant_id=plant_id.strip(),
                )

                st.success("Run completed.")
                st.caption(
                    f"Payloads sent: iLPN={result['ilpn_payload_count']} | oLPN={result['olpn_payload_count']}"
                )

                st.subheader("iLPN Results")
                if result["ilpn_df"].empty:
                    st.info("No iLPN rows returned.")
                else:
                    st.dataframe(result["ilpn_df"], use_container_width=True)

                st.subheader("oLPN Results")
                if result["olpn_df"].empty:
                    st.info("No oLPN rows returned.")
                else:
                    st.dataframe(result["olpn_df"], use_container_width=True)

                st.download_button(
                    label="Download Excel Output",
                    data=result["excel_bytes"],
                    file_name=result["excel_name"],
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            except Exception as exc:
                st.error(f"Failed to run MHE Journal: {exc}")