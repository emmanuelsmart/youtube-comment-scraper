#!/bin/bash
pip install streamlit pandas playwright requests
playwright install --with-deps
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
