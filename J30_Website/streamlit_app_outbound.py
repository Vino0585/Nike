import streamlit as st

from Outbound.MHE_Journal_Outbound_Copy import MHEJournalOutboundCopy
from Outbound.Order_Search_Copy import OrderSearchCopy
from Outbound.Wave_Information_Copy import WaveInformationCopy


def _parse_semicolon_values(raw_value: str) -> list[str]:
	values = [item.strip() for item in raw_value.split(";")]
	values = [item for item in values if item]
	return list(dict.fromkeys(values))


st.set_page_config(page_title="Outbound Utilities", page_icon="📦", layout="wide")
st.title("AWM Outbound Utilities")
st.write("Use tabs for the tools user wants to utilize.")

tab_mhe, tab_order, tab_wave = st.tabs(
	["MHE Journal Outbound", "Order Search", "Wave Information"]
)


with tab_mhe:
	st.subheader("MHE Journal Outbound by Wave")
	st.write("Run outbound MHE journal for a wave number and download the Excel result.")

	with st.form("mhe_wave_form"):
		wave_number = st.text_input("Wave Number", placeholder="Example: 12345678")
		environment = st.selectbox("Environment", options=["qa", "prod", "dev"], index=0, key="mhe_env")
		plant_id = st.text_input("Plant", value="1081", key="mhe_plant")
		mhe_submitted = st.form_submit_button("Run MHE Journal")

	if mhe_submitted:
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


with tab_order:
	st.subheader("Order Search")
	order_search_mode = st.radio(
		"Order Search Type",
		options=["original_order_search", "parent_order_search"],
		format_func=lambda value: value.replace("_", " ").title(),
		horizontal=True,
	)
	if order_search_mode == "original_order_search":
		st.write("Enter one or more original order IDs separated by `;`.")
	else:
		st.write("Enter one or more original order IDs separated by `;` to retrieve parent-order results.")

	with st.form("order_search_form"):
		order_text = st.text_area(
			"Order IDs",
			placeholder="Example: 0000123456;0000123457;0000123458",
			height=80,
		)
		order_environment = st.selectbox(
			"Environment",
			options=["qa", "prod", "dev"],
			index=0,
			key="order_env",
		)
		order_plant_id = st.text_input("Plant", value="1081", key="order_plant")
		order_submitted = st.form_submit_button("Run Order Search")

	if order_submitted:
		order_ids = _parse_semicolon_values(order_text or "")

		if not order_ids:
			st.error("Provide at least one Order ID.")
		elif not order_plant_id.strip():
			st.error("Plant is required.")
		else:
			with st.spinner("Running order search..."):
				try:
					result = OrderSearchCopy().run_for_orders(
						environment=order_environment.strip(),
						plant_id=order_plant_id.strip(),
						order_ids=order_ids,
						search_mode=order_search_mode,
					)
					order_df = result["df"]

					st.caption(
						f"Search type: {result['search_mode'].replace('_', ' ').title()} | Inputs received: {result['input_count']} | Queries sent: {result['request_count']}"
					)
					if order_df.empty:
						st.info("No order rows returned.")
					else:
						st.success(f"Found {len(order_df)} row(s).")
						st.dataframe(order_df, use_container_width=True)

					st.download_button(
						label="Download Order Search Output",
						data=result["excel_bytes"],
						file_name=result["excel_name"],
						mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
					)
				except Exception as exc:
					st.error(f"Failed to run Order Search: {exc}")


with tab_wave:
	st.subheader("Wave Information")
	st.write("Enter one or more wave numbers separated by `;`.")

	with st.form("wave_information_form"):
		wave_text = st.text_area(
			"Wave Numbers",
			placeholder="Example: 12345678;12345679",
			height=80,
		)
		wave_environment = st.selectbox(
			"Environment",
			options=["qa", "prod", "dev"],
			index=0,
			key="wave_env",
		)
		wave_plant_id = st.text_input("Plant", value="1081", key="wave_plant")
		wave_submitted = st.form_submit_button("Run Wave Information")

	if wave_submitted:
		wave_numbers = _parse_semicolon_values(wave_text or "")

		if not wave_numbers:
			st.error("Provide at least one Wave Number.")
		elif not wave_plant_id.strip():
			st.error("Plant is required.")
		else:
			with st.spinner("Running wave information search..."):
				try:
					result = WaveInformationCopy().run_for_waves(
						environment=wave_environment.strip(),
						plant_id=wave_plant_id.strip(),
						wave_numbers=wave_numbers,
					)
					wave_df = result["df"]

					st.caption(
						f"Inputs received: {result['input_count']} | Queries sent: {result['request_count']}"
					)
					if wave_df.empty:
						st.info("No wave rows returned.")
					else:
						st.success(f"Found {len(wave_df)} row(s).")
						st.dataframe(wave_df, use_container_width=True)

					st.download_button(
						label="Download Wave Information Output",
						data=result["excel_bytes"],
						file_name=result["excel_name"],
						mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
					)
				except Exception as exc:
					st.error(f"Failed to run Wave Information: {exc}")

