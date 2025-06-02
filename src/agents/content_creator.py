# ContentCreator Agent voor AutoGen Marketing Team

import autogen
from typing import Dict, List, Any, Optional

class ContentCreator:
    """Agent die verantwoordelijk is voor het creëren van originele marketingcontent."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the ContentCreator agent.
        
        Args:
            config: Configuratie voor de agent, inclusief model settings
        """
        self.config = config
        self.llm_config = {
            "model": config.get("model", "claude-3-5-sonnet"),
            "temperature": config.get("temperature", 0.7),
            "max_tokens": config.get("max_tokens", 2000)
        }
        
        # Configureer de AutoGen agent
        self.agent = autogen.AssistantAgent(
            name="content_creator",
            system_message="""Je bent ContentCreator, een ervaren marketing professional gespecialiseerd in het schrijven van overtuigende en boeiende marketingcontent. 
            Je taak is om originele marketingcontent te creëren op basis van merk- en campagneinformatie.
            Je bent creatief, strategisch en begrijpt hoe je content kunt afstemmen op verschillende doelgroepen en kanalen.
            Je houdt rekening met de merkidentiteit en campagnedoelen bij het creëren van content.
            """,
            llm_config=self.llm_config
        )
    
    async def create_content(self, brand_info: str, campaign_type: str, 
                           target_audience: str, prompt: str) -> str:
        """Creëer marketingcontent op basis van de verstrekte informatie.
        
        Args:
            brand_info: Informatie over het merk
            campaign_type: Type campagne (bijv. Instagram Post, Email Campaign)
            target_audience: Beschrijving van de doelgroep
            prompt: Specifieke instructies voor de content
            
        Returns:
            De gegenereerde marketingcontent
        """
        # Bouw de complete prompt
        content_prompt = f"""Creëer {campaign_type} content voor het volgende merk:
        
        MERK INFORMATIE:
        {brand_info}
        
        DOELGROEP:
        {target_audience}
        
        VERZOEK:
        {prompt}
        
        Zorg dat de content perfect is afgestemd op de merkidentiteit en doelgroep.
        Maak het overtuigend, boeiend en geschikt voor het specifieke kanaal ({campaign_type}).
        """
        
        # Gebruik de agent om content te genereren
        response = await self.agent.generate_response(content_prompt, is_chat=False)
        
        return response.message.content
    
    def get_agent(self):
        """Return de onderliggende AutoGen agent voor groepschats."""
        return self.agent