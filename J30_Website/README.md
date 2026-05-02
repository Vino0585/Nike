# MHE Journal Streamlit Runner

This adds a Streamlit UI to run outbound MHE Journal by wave number without changing the original `Outbound/MHE_Journal_Outbound.py`.

## Added Files

- `Outbound/MHE_Journal_Outbound_Copy.py`: Copy-style implementation for wave-driven execution and in-memory Excel output.
- `streamlit_app.py`: UI to collect wave input and download Excel results.
- `requirements.txt`: Minimal dependencies for this flow.

## Run

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## How it Works

1. UI collects `Wave Number`, `Environment`, and `Plant`.
2. `Outbound/MHE_Journal_Outbound_Copy.py` calls task-detail API by wave.
3. It runs iLPN and oLPN message-journal searches.
4. It returns two result tables and a downloadable workbook.

