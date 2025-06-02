# Streamlit Web Interface voor AutoGen Marketing Team

import streamlit as st
import sys
import os
import asyncio
import json
from typing import Dict, Any

# Voeg de src directory toe aan sys.path zodat we de modules kunnen importeren
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.main import MarketingTeam
from src.web.components.header import render_header
from src.web.components.sidebar import render_sidebar
from src.web.components.form import render_form
from src.web.components.results import render_results
from src.web.components.processing import process_with_animation

# Pagina configuratie
st.set_page_config(
    page_title="🎯 AI Marketing Team",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hoofdfunctie voor de app
async def main():
    # Render de header
    render_header()
    
    # Render de sidebar
    render_sidebar()
    
    # Render het formulier en krijg de input
    submit_pressed, form_data = render_form()
    
    # Als de submit knop is ingedrukt en alle vereiste velden zijn ingevuld
    if submit_pressed:
        if not form_data["brand_info"] or not form_data["target_audience"] or not form_data["prompt"]:
            st.error("Vul alle velden in om content te genereren.")
        else:
            # Initialiseer MarketingTeam
            marketing_team = MarketingTeam()
            
            # Process met animatie
            results = await process_with_animation(
                marketing_team.run,
                prompt=form_data["prompt"],
                campaign_type=form_data["campaign_type"],
                brand_info=form_data["brand_info"],
                target_audience=form_data["target_audience"]
            )
            
            # Render de resultaten
            render_results(results)

# Streamlit app entry point
if __name__ == "__main__":
    # Voer de app asynchroon uit met asyncio
    asyncio.run(main())