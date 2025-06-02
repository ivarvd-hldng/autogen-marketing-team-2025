# MarketingReviewer Agent voor AutoGen Marketing Team

import autogen
from typing import Dict, List, Any, Optional

class MarketingReviewer:
    """Agent die verantwoordelijk is voor het beoordelen en verbeteren van marketingcontent."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the MarketingReviewer agent.
        
        Args:
            config: Configuratie voor de agent, inclusief model settings
        """
        self.config = config
        self.llm_config = {
            "model": config.get("model", "claude-3-5-sonnet"),
            "temperature": config.get("temperature", 0.3),
            "max_tokens": config.get("max_tokens", 2000)
        }
        
        # Configureer de AutoGen agent
        self.agent = autogen.AssistantAgent(
            name="marketing_reviewer",
            system_message="""Je bent MarketingReviewer, een marketing expert gespecialiseerd in het beoordelen en verbeteren van marketingcontent. 
            Je taak is om marketingcontent kritisch te beoordelen en concrete verbeteringen voor te stellen.
            Je hebt expertise in copywriting, branding, marketingstrategie en doelgroepanalyse.
            Je beoordeelt content op effectiviteit, merkwaarden, tone of voice, en conversiedoelen.
            """,
            llm_config=self.llm_config
        )
    
    async def review_content(self, content: str, brand_info: str, 
                          campaign_type: str, target_audience: str) -> Dict[str, Any]:
        """Beoordeel en verbeter de marketingcontent.
        
        Args:
            content: De te beoordelen marketingcontent
            brand_info: Informatie over het merk
            campaign_type: Type campagne (bijv. Instagram Post, Email Campaign)
            target_audience: Beschrijving van de doelgroep
            
        Returns:
            Dict met beoordeling, verbeterpunten en verbeterde content
        """
        # Bouw de review prompt
        review_prompt = f"""Beoordeel en verbeter de volgende {campaign_type} content:
        
        CONTENT:
        {content}
        
        MERK INFORMATIE:
        {brand_info}
        
        DOELGROEP:
        {target_audience}
        
        Geef een gestructureerde beoordeling met:
        1. Algemene indruk (schaal 1-10)
        2. Sterke punten
        3. Verbeterpunten
        4. Verbeterde versie van de content
        5. Uitleg van de wijzigingen
        
        Zorg dat de verbeterde content perfect aansluit bij de merkidentiteit en doelgroep.
        """
        
        # Gebruik de agent om de beoordeling te genereren
        response = await self.agent.generate_response(review_prompt, is_chat=False)
        result = response.message.content
        
        # Parse de resultaten (vereenvoudigd, in werkelijkheid zou je een meer robuuste parser gebruiken)
        # Hier splitsen we het gewoon op secties
        sections = result.split("\n\n")
        
        try:
            # Probeer de score te extraheren
            score_line = next((s for s in sections if "schaal" in s.lower()), "")
            score = int(score_line.split("/")[0].strip()[-1]) if "/" in score_line else \
                   int(next((c for c in score_line if c.isdigit()), 0))
            
            # Zoek verbeterde content
            improved_content_idx = next((i for i, s in enumerate(sections) 
                                     if "verbeterde versie" in s.lower() or 
                                     "verbeterde content" in s.lower()), -1)
            
            improved_content = sections[improved_content_idx + 1] if improved_content_idx >= 0 and \
                              improved_content_idx + 1 < len(sections) else ""
            
            return {
                "score": score,
                "review": result,
                "improved_content": improved_content
            }
        except Exception as e:
            # Als parsing faalt, geef de volledige review terug
            return {
                "score": 0,
                "review": result,
                "improved_content": "",
                "error": str(e)
            }
    
    def get_agent(self):
        """Return de onderliggende AutoGen agent voor groepschats."""
        return self.agent