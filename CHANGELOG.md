# Changelog

Alle belangrijke wijzigingen in dit project worden gedocumenteerd in dit bestand.

Het format is gebaseerd op [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
en dit project volgt [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-06-02

### Toegevoegd
- Initiële release van het AutoGen Marketing Team
- ContentCreator agent voor het genereren van originele marketingcontent
- MarketingReviewer agent voor het beoordelen en verbeteren van content
- Streamlit web interface voor gebruiksvriendelijke interactie
- API voor externe integratie
- WebSocket ondersteuning voor real-time agent communicatie
- Cloudflare Workers deployment voor edge performance
- Heroku deployment voor managed inference
- Documentatie in de `/docs` directory

### Technisch
- Implementatie van AutoGen framework voor multi-agent samenwerking
- Claude 3.5 Sonnet als basis LLM
- MCP server voor deployment en beheer
- Configureerbare agent parameters
- Rate limiting en authenticatie voor de API
- Docker support voor containerization
- CI/CD workflows via GitHub Actions
