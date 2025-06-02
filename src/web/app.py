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

# Pagina configuratie
st.set_page_config(
    page_title="🎯 AI Marketing Team",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Titel en beschrijving
st.title("🎯 AI Marketing Team")
st.markdown("Een **volledig geautomatiseerd** marketing team met twee AI-agents die samenwerken om hoogwaardige content te creëren en te verbeteren.")

# Sidebar met uitleg
with st.sidebar:
    st.header("🤖 Over de AI Agents")
    st.markdown("""
    Dit systeem bestaat uit twee gespecialiseerde AI-agents:
    
    **ContentCreator** 🎨
    - Genereert originele marketingcontent
    - Afgestemd op merk en doelgroep
    - Geoptimaliseerd voor campagnetype
    
    **MarketingReviewer** 🔍
    - Beoordeelt de gegenereerde content
    - Stelt verbeteringen voor
    - Zorgt voor optimale marketingeffectiviteit
    """)
    
    st.header("⚙️ Technologie")
    st.markdown("""
    - **AutoGen** framework voor multi-agent samenwerking
    - **Claude 3.5 Sonnet** als basis LLM
    - **Cloudflare Workers** voor edge performance
    - **Heroku MCP Platform** voor managed inference
    """)

# Hoofdformulier
st.header("📝 Creëer Marketingcontent")

# Inputvelden
col1, col2 = st.columns(2)

with col1:
    campaign_type = st.selectbox(
        "Campagnetype",
        ["Instagram Post", "Email Campaign", "LinkedIn Content", "Facebook Ad", "Twitter/X Post", "TikTok Script", "Blog Artikel", "Persbericht"]
    )
    
    brand_info = st.text_area(
        "Merkinformatie",
        placeholder="Beschrijf je merk: naam, missie, waarden, tone of voice, etc.",
        height=150
    )

with col2:
    target_audience = st.text_area(
        "Doelgroep",
        placeholder="Beschrijf je doelgroep: leeftijd, interesses, pijnpunten, etc.",
        height=75
    )
    
    prompt = st.text_area(
        "Opdracht",
        placeholder="Wat wil je creëren? Bijv: 'Een Instagram post over onze nieuwe productserie'",
        height=75
    )

# Knop om het proces te starten
if st.button("🚀 Genereer Marketingcontent", type="primary"):
    if not brand_info or not target_audience or not prompt:
        st.error("Vul alle velden in om content te genereren.")
    else:
        # Initialiseer MarketingTeam
        marketing_team = MarketingTeam()
        
        # Progress bar en status update
        progress_bar = st.progress(0)
        status_container = st.empty()
        
        # Functie om het process asynchroon uit te voeren
        async def run_marketing_team():
            status_container.markdown("⏳ **Stap 1/2:** ContentCreator genereert originele content...")
            progress_bar.progress(25)
            
            # Run het marketing team
            results = await marketing_team.run(
                prompt=prompt,
                campaign_type=campaign_type,
                brand_info=brand_info,
                target_audience=target_audience
            )
            
            status_container.markdown("⏳ **Stap 2/2:** MarketingReviewer beoordeelt en verbetert de content...")
            progress_bar.progress(75)
            
            # Simuleer wat vertraging voor de gebruikerservaring
            await asyncio.sleep(1)
            
            progress_bar.progress(100)
            status_container.markdown("✅ **Voltooid!** Content is gegenereerd en verbeterd.")
            
            return results
        
        # Run de asyncio functie
        results = asyncio.run(run_marketing_team())
        
        # Toon de resultaten
        st.subheader("🤖 Agent Samenwerking")
        
        tab1, tab2 = st.tabs(["Originele Content", "Verbeterde Content"])
        
        with tab1:
            st.markdown("### 🎨 Content van ContentCreator")
            st.markdown(results["original_content"])
        
        with tab2:
            st.markdown("### 🔍 Feedback van MarketingReviewer")
            st.markdown(results["review"])
            
            st.markdown("### ✨ Verbeterde Content")
            st.markdown(results["improved_content"])
        
        # Voeg statistieken toe
        st.subheader("📊 Statistieken")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Content Score", f"{results['score']}/10")
        
        with col2:
            # Bereken geschatte kosten op basis van tokengebruik (gesimuleerd)
            # In werkelijkheid zou je dit berekenen op basis van het werkelijke API-gebruik
            estimated_tokens = len(prompt) + len(brand_info) + len(target_audience) + \
                              len(results["original_content"]) + len(results["review"]) + \
                              len(results["improved_content"])
            estimated_tokens = estimated_tokens // 4  # Ruwe schatting van tokens
            estimated_cost = estimated_tokens * 0.000008  # Claude 3.5 Sonnet prijs per token
            
            st.metric("Geschatte Kosten", f"€{estimated_cost:.4f}")
        
        with col3:
            st.metric("Campagnetype", campaign_type)
        
        # Downloadknoppen
        st.subheader("💾 Download Resultaten")
        
        # Creëer downloadbare bestanden
        original_content_str = results["original_content"]
        improved_content_str = results["improved_content"]
        full_results_str = json.dumps(results, indent=2)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.download_button(
                label="📄 Download Originele Content",
                data=original_content_str,
                file_name="originele_content.txt",
                mime="text/plain"
            )
        
        with col2:
            st.download_button(
                label="📄 Download Verbeterde Content",
                data=improved_content_str,
                file_name="verbeterde_content.txt",
                mime="text/plain"
            )
        
        with col3:
            st.download_button(
                label="📊 Download Volledige Resultaten (JSON)",
                data=full_results_str,
                file_name="marketing_results.json",
                mime="application/json"
            )

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: gray; font-size: 12px;">
    🚀 Aangedreven door AutoGen en Claude 3.5 Sonnet | 🌐 Edge Deployment via Cloudflare Workers | 🔧 Managed door Heroku MCP Platform
</div>
""", unsafe_allow_html=True)