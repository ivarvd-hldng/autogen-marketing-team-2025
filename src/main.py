# Main Application voor AutoGen Marketing Team

import os
import json
import asyncio
import autogen
from typing import Dict, List, Any, Optional

from agents.content_creator import ContentCreator
from agents.marketing_reviewer import MarketingReviewer
from tools.search_tools import SearchTools
from tools.content_tools import ContentTools
from mcp.server import MCPServer

class MarketingTeam:
    """Hoofdklasse voor het AutoGen Marketing Team."""
    
    def __init__(self, config_path: str = "config/config.json"):
        """Initialize het marketing team.
        
        Args:
            config_path: Pad naar het configuratiebestand
        """
        # Laad configuratie
        self.config = self._load_config(config_path)
        
        # Initialiseer tools
        self.search_tools = SearchTools(self.config.get("search_tools", {}))
        self.content_tools = ContentTools(self.config.get("content_tools", {}))
        
        # Initialiseer agents
        self.content_creator = ContentCreator(self.config.get("content_creator", {}))
        self.marketing_reviewer = MarketingReviewer(self.config.get("marketing_reviewer", {}))
        
        # Initialiseer MCP server (indien geconfigureerd)
        self.mcp_server = None
        if self.config.get("use_mcp", False):
            self.mcp_server = MCPServer(self.config.get("mcp", {}))
        
        print("AutoGen Marketing Team geïnitialiseerd")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Laad configuratie uit bestand.
        
        Args:
            config_path: Pad naar configuratiebestand
            
        Returns:
            Dict met configuratie
        """
        # Als het configuratiebestand niet bestaat, gebruik standaardconfiguratie
        if not os.path.exists(config_path):
            print(f"Configuratiebestand {config_path} niet gevonden, standaardconfiguratie gebruiken")
            return {
                "content_creator": {
                    "model": "claude-3-5-sonnet",
                    "temperature": 0.7
                },
                "marketing_reviewer": {
                    "model": "claude-3-5-sonnet",
                    "temperature": 0.3
                },
                "search_tools": {},
                "content_tools": {},
                "use_mcp": False
            }
        
        # Laad configuratie uit bestand
        with open(config_path, "r") as f:
            return json.load(f)
    
    async def run(self, prompt: str, campaign_type: str, 
                brand_info: str, target_audience: str) -> Dict[str, Any]:
        """Run het marketing team om content te genereren en te verbeteren.
        
        Args:
            prompt: Specifieke instructies voor de content
            campaign_type: Type campagne (bijv. Instagram Post, Email Campaign)
            brand_info: Informatie over het merk
            target_audience: Beschrijving van de doelgroep
            
        Returns:
            Dict met resultaten, inclusief originele en verbeterde content
        """
        print(f"Start marketing team voor {campaign_type}")
        
        # Stap 1: Content Creator genereert de initiële content
        print("Stap 1: Content genereren...")
        original_content = await self.content_creator.create_content(
            brand_info, campaign_type, target_audience, prompt
        )
        
        # Stap 2: Marketing Reviewer beoordeelt en verbetert de content
        print("Stap 2: Content beoordelen en verbeteren...")
        review_results = await self.marketing_reviewer.review_content(
            original_content, brand_info, campaign_type, target_audience
        )
        
        # Verzamel resultaten
        results = {
            "original_content": original_content,
            "review": review_results.get("review", ""),
            "score": review_results.get("score", 0),
            "improved_content": review_results.get("improved_content", ""),
            "campaign_type": campaign_type,
            "timestamp": "2025-06-02",  # In werkelijkheid zou je datetime.now() gebruiken
        }
        
        print("Marketing team klaar")
        return results
    
    async def setup_group_chat(self):
        """Configureer een groepschat tussen agents voor meer complexe taken."""
        # Haal de agent-instanties op
        content_creator_agent = self.content_creator.get_agent()
        marketing_reviewer_agent = self.marketing_reviewer.get_agent()
        
        # Maak een UserProxyAgent voor menselijke input
        user_proxy = autogen.UserProxyAgent(
            name="user_proxy",
            is_termination_msg=lambda msg: "TAAK VOLTOOID" in msg.get("content", "")
        )
        
        # Configureer de groepschat
        groupchat = autogen.GroupChat(
            agents=[user_proxy, content_creator_agent, marketing_reviewer_agent],
            messages=[],
            max_round=10
        )
        
        # Maak een manager voor de groepschat
        manager = autogen.GroupChatManager(groupchat=groupchat)
        
        return {
            "user_proxy": user_proxy,
            "manager": manager,
            "groupchat": groupchat
        }

async def deploy_mcp():
    """Deploy het systeem naar MCP (Cloudflare/Heroku)."""
    # Laad MCP-specifieke configuratie
    config = {
        "mcp": {
            "cloudflare": {
                "account_id": os.environ.get("CLOUDFLARE_ACCOUNT_ID", ""),
                "api_token": os.environ.get("CLOUDFLARE_API_TOKEN", ""),
                "zone_id": os.environ.get("CLOUDFLARE_ZONE_ID", "")
            },
            "heroku": {
                "api_key": os.environ.get("HEROKU_API_KEY", ""),
                "app_name": "autogen-marketing-team"
            },
            "debug_mode": True
        }
    }
    
    # Initialiseer en deploy de MCP server
    mcp_server = MCPServer(config["mcp"])
    await mcp_server.initialize()
    await mcp_server.deploy()

async def main():
    """Hoofdfunctie voor het starten van het systeem."""
    # Initialiseer het marketing team
    marketing_team = MarketingTeam()
    
    # Voorbeeld van het runnen van het team
    results = await marketing_team.run(
        prompt="Creëer een Instagram post die onze nieuwe eco-vriendelijke productlijn promoot",
        campaign_type="Instagram Post",
        brand_info="GreenTech is een duurzaam technologiebedrijf dat focust op milieuvriendelijke gadgets",
        target_audience="Milieubewuste consumenten tussen 25-40 jaar die geïnteresseerd zijn in technologie"
    )
    
    # Print resultaten
    print("\nOriginele Content:")
    print(results["original_content"])
    print("\nBeoordeling:")
    print(results["review"])
    print("\nVerbeterde Content:")
    print(results["improved_content"])
    
    # Deploy MCP als omgevingsvariabelen zijn ingesteld
    if os.environ.get("DEPLOY_MCP", "").lower() == "true":
        await deploy_mcp()

if __name__ == "__main__":
    asyncio.run(main())