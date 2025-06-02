# 🎯 AutoGen Marketing Team (2025)

Een volledig geautomatiseerd marketingteam gebouwd met AutoGen en Claude. Dit systeem bestaat uit twee AI-agents die samenwerken om hoogwaardige marketingcontent te creëren en te verbeteren.

## 🚀 Agents

- **ContentCreator**: Schrijft originele marketingcontent op basis van merk- en campagne-informatie
- **MarketingReviewer**: Beoordeelt en verbetert de content met marketing expertise

## 🌐 Implementatie

Dit project bevat:

- Volledige AutoGen implementatie
- Cloudflare Workers deployment voor edge performance
- Heroku MCP Platform integratie
- Streamlit web interface
- Geavanceerde automatiseringsfuncties

## 🔧 Tech Stack

- **Python** + **AutoGen** voor de agent architectuur
- **Cloudflare Workers** voor edge deployment
- **Heroku** voor managed inference
- **Streamlit** voor de web interface
- **Claude 3.5 Sonnet** als basis LLM

## 📋 Aan de slag

1. Clone de repository
2. Installeer de vereisten: `pip install -r requirements.txt`
3. Configureer je API keys in `.env`
4. Start de lokale ontwikkelomgeving: `python src/main.py`
5. Open de web interface: `streamlit run src/web/app.py`

## 🔍 Project Structuur

```
autogen-marketing-team/
├── src/
│   ├── agents/
│   │   ├── content_creator.py
│   │   └── marketing_reviewer.py
│   ├── tools/
│   │   ├── search_tools.py
│   │   └── content_tools.py
│   ├── mcp/
│   │   └── server.py
│   └── main.py
├── config/
│   ├── cloudflare.toml
│   └── heroku.yml
├── deployment/
│   ├── Dockerfile
│   └── requirements.txt
├── docs/
├── .env.example
├── README.md
└── package.json
```

## 📊 Prestaties

- Global edge deployment (< 50ms response)
- Real-time agent collaboration
- Kostefficiënt (vanaf ~€7/maand)
- Enterprise-grade beveiliging

## 📚 Documentatie

Bekijk de `/docs` directory voor gedetailleerde instructies en API documentatie.

## 🔒 Licentie

MIT