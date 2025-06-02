# Deploy script voor het AutoGen Marketing Team MCP

import os
import sys
import asyncio
import logging
import subprocess
import requests
import json
from typing import Dict, Any, List, Optional

# Voeg de src directory toe aan sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.mcp.server import MCPServer

# Configureer logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("deploy")

async def deploy_to_cloudflare(config: Dict[str, Any]) -> str:
    """Deploy naar Cloudflare Workers.
    
    Args:
        config: Cloudflare configuratie
        
    Returns:
        str: De URL van de gedeployde Worker
    """
    logger.info("Deploying naar Cloudflare Workers...")
    
    # Controleer of alle vereiste configuratie aanwezig is
    required_keys = ["account_id", "api_token", "zone_id"]
    missing_keys = [key for key in required_keys if not config.get(key)]
    
    if missing_keys:
        raise ValueError(f"Ontbrekende vereiste configuratie: {', '.join(missing_keys)}")
    
    # Configureer omgevingsvariabelen voor wrangler
    env = os.environ.copy()
    env["CLOUDFLARE_ACCOUNT_ID"] = config["account_id"]
    env["CLOUDFLARE_API_TOKEN"] = config["api_token"]
    
    # Controleer of wrangler is geïnstalleerd
    try:
        subprocess.run(["npx", "wrangler", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        logger.info("Wrangler niet gevonden, installeren...")
        subprocess.run(["npm", "install", "wrangler", "--no-save"], check=True)
    
    # Genereer wrangler.toml bestand
    wrangler_config = f"""
name = "autogen-marketing-team"
type = "javascript"
usage_model = "bundled"
workers_dev = true
compatibility_date = "2025-06-01"
account_id = "{config['account_id']}"
zone_id = "{config['zone_id']}"

[build]
command = "npm run build"

[build.upload]
format = "service-worker"

[durable_objects]
class_names = ["AgentStateStore"]

[[kv_namespaces]]
binding = "AGENT_DATA"
id = "{config.get('kv_namespace_id', '')}"

[env.production]
name = "autogen-marketing-team"
"""
    
    with open("wrangler.toml", "w") as f:
        f.write(wrangler_config)
    
    # Kopieer cloudflare_worker.js naar src/index.js voor wrangler
    os.makedirs("src", exist_ok=True)
    with open("src/mcp/cloudflare_worker.js", "r") as src_file:
        with open("src/index.js", "w") as dest_file:
            dest_file.write(src_file.read())
    
    # Maak package.json als het nog niet bestaat
    if not os.path.exists("package.json"):
        package_json = {
            "name": "autogen-marketing-team",
            "version": "1.0.0",
            "description": "AutoGen Marketing Team Cloudflare Worker",
            "main": "src/index.js",
            "scripts": {
                "build": "webpack",
                "deploy": "wrangler publish"
            },
            "dependencies": {
                "itty-router": "^4.0.23",
                "toucan-js": "^2.7.0"
            },
            "devDependencies": {
                "webpack": "^5.89.0",
                "webpack-cli": "^5.1.4"
            }
        }
        
        with open("package.json", "w") as f:
            json.dump(package_json, f, indent=2)
    
    # Maak webpack.config.js
    webpack_config = """
module.exports = {
  entry: './src/index.js',
  mode: 'production',
  target: 'webworker',
  output: {
    filename: 'worker.js',
    path: __dirname + '/dist'
  }
};
"""
    
    with open("webpack.config.js", "w") as f:
        f.write(webpack_config)
    
    # Installeer dependencies
    logger.info("Installeren van dependencies...")
    subprocess.run(["npm", "install"], check=True)
    
    # Deploy naar Cloudflare Workers
    logger.info("Deploying naar Cloudflare Workers...")
    result = subprocess.run(
        ["npx", "wrangler", "publish", "--env", "production"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=True
    )
    
    # Parse de URL uit de output
    output = result.stdout
    worker_url = ""
    for line in output.split("\n"):
        if "https://" in line and "workers.dev" in line:
            worker_url = line.strip()
            break
    
    if not worker_url:
        worker_url = f"https://autogen-marketing-team.{config['account_id']}.workers.dev"
    
    logger.info(f"Succesvol gedeployed naar Cloudflare Workers: {worker_url}")
    return worker_url

async def deploy_to_heroku(config: Dict[str, Any]) -> str:
    """Deploy naar Heroku.
    
    Args:
        config: Heroku configuratie
        
    Returns:
        str: De URL van de gedeployde app
    """
    logger.info("Deploying naar Heroku...")
    
    # Controleer of alle vereiste configuratie aanwezig is
    required_keys = ["api_key", "app_name"]
    missing_keys = [key for key in required_keys if not config.get(key)]
    
    if missing_keys:
        raise ValueError(f"Ontbrekende vereiste configuratie: {', '.join(missing_keys)}")
    
    # Controleer of Heroku CLI is geïnstalleerd
    try:
        subprocess.run(["heroku", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("Heroku CLI niet gevonden. Proberen via API requests...")
        return await deploy_to_heroku_api(config)
    
    # Configureer Heroku credentials
    env = os.environ.copy()
    env["HEROKU_API_KEY"] = config["api_key"]
    
    # Controleer of de app al bestaat
    result = subprocess.run(
        ["heroku", "apps:info", "--app", config["app_name"]],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=True
    )
    
    app_exists = result.returncode == 0
    
    if not app_exists:
        # Maak de app aan
        logger.info(f"App {config['app_name']} bestaat nog niet, aanmaken...")
        subprocess.run(
            ["heroku", "apps:create", config["app_name"]],
            check=True,
            env=env
        )
    
    # Voeg Heroku PostgreSQL add-on toe
    logger.info("PostgreSQL add-on toevoegen...")
    subprocess.run(
        ["heroku", "addons:create", "heroku-postgresql:hobby-dev", "--app", config["app_name"]],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env
    )
    
    # Configureer omgevingsvariabelen
    logger.info("Omgevingsvariabelen configureren...")
    env_vars = {
        "ENVIRONMENT": "production",
        "PYTHONUNBUFFERED": "1",
        "WEB_CONCURRENCY": "4",
        "AUTOGEN_DEBUG": "false",
        "AI_PROVIDER": "claude",
        "AI_MODEL": "claude-3-5-sonnet",
        "ENABLE_MCP": "true",
        "CLAUDE_API_KEY": os.environ.get("CLAUDE_API_KEY", "")
    }
    
    env_command = ["heroku", "config:set", "--app", config["app_name"]]
    for key, value in env_vars.items():
        env_command.append(f"{key}={value}")
    
    subprocess.run(env_command, check=True, env=env)
    
    # Maak Procfile als het nog niet bestaat
    if not os.path.exists("Procfile"):
        with open("Procfile", "w") as f:
            f.write("""web: gunicorn src.api.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --log-file -
worker: python src/worker.py
mcp_server: python src/mcp/server.py
""")
    
    # Configureer git remote voor Heroku
    subprocess.run(
        ["git", "remote", "rm", "heroku"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    subprocess.run(
        ["git", "remote", "add", "heroku", f"https://git.heroku.com/{config['app_name']}.git"],
        check=True
    )
    
    # Push naar Heroku
    logger.info("Deploying naar Heroku...")
    subprocess.run(
        ["git", "push", "heroku", "main:main", "--force"],
        check=True,
        env=env
    )
    
    # Run database migraties
    logger.info("Database migraties uitvoeren...")
    subprocess.run(
        ["heroku", "run", "python", "src/db/migrations.py", "--app", config["app_name"]],
        check=True,
        env=env
    )
    
    app_url = f"https://{config['app_name']}.herokuapp.com"
    logger.info(f"Succesvol gedeployed naar Heroku: {app_url}")
    return app_url

async def deploy_to_heroku_api(config: Dict[str, Any]) -> str:
    """Deploy naar Heroku via de API in plaats van de CLI.
    
    Args:
        config: Heroku configuratie
        
    Returns:
        str: De URL van de gedeployde app
    """
    logger.info("Deploying naar Heroku via API...")
    
    api_key = config["api_key"]
    app_name = config["app_name"]
    headers = {
        "Accept": "application/vnd.heroku+json; version=3",
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Controleer of de app al bestaat
    app_response = requests.get(
        f"https://api.heroku.com/apps/{app_name}",
        headers=headers
    )
    
    if app_response.status_code == 404:
        # Maak de app aan
        logger.info(f"App {app_name} bestaat nog niet, aanmaken...")
        app_response = requests.post(
            "https://api.heroku.com/apps",
            headers=headers,
            json={
                "name": app_name,
                "stack": "heroku-22"
            }
        )
        
        if app_response.status_code != 201:
            raise ValueError(f"Kon app niet aanmaken: {app_response.text}")
    
    # Voeg PostgreSQL add-on toe
    logger.info("PostgreSQL add-on toevoegen...")
    addon_response = requests.post(
        f"https://api.heroku.com/apps/{app_name}/addons",
        headers=headers,
        json={
            "plan": "heroku-postgresql:hobby-dev"
        }
    )
    
    # Configureer omgevingsvariabelen
    logger.info("Omgevingsvariabelen configureren...")
    env_vars = {
        "ENVIRONMENT": "production",
        "PYTHONUNBUFFERED": "1",
        "WEB_CONCURRENCY": "4",
        "AUTOGEN_DEBUG": "false",
        "AI_PROVIDER": "claude",
        "AI_MODEL": "claude-3-5-sonnet",
        "ENABLE_MCP": "true",
        "CLAUDE_API_KEY": os.environ.get("CLAUDE_API_KEY", "")
    }
    
    config_response = requests.patch(
        f"https://api.heroku.com/apps/{app_name}/config-vars",
        headers=headers,
        json=env_vars
    )
    
    if config_response.status_code != 200:
        logger.warning(f"Kon omgevingsvariabelen niet configureren: {config_response.text}")
    
    # Deployment via API vereist een tarball of GitHub integratie
    # Dit is complexer dan via de CLI, dus we geven een instructie
    logger.info("""Heroku API deployment zonder CLI vereist extra stappen:
    1. Installeer de Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli
    2. Login: heroku login
    3. Deploy: git push heroku main:main
    
    Of deploy via de GitHub integratie in het Heroku dashboard.""")
    
    app_url = f"https://{app_name}.herokuapp.com"
    return app_url

async def main():
    """Hoofdfunctie voor deployment."""
    # Laad configuratie uit omgevingsvariabelen
    config = {
        "mcp": {
            "cloudflare": {
                "account_id": os.environ.get("CLOUDFLARE_ACCOUNT_ID", ""),
                "api_token": os.environ.get("CLOUDFLARE_API_TOKEN", ""),
                "zone_id": os.environ.get("CLOUDFLARE_ZONE_ID", ""),
                "kv_namespace_id": os.environ.get("CLOUDFLARE_KV_NAMESPACE_ID", "")
            },
            "heroku": {
                "api_key": os.environ.get("HEROKU_API_KEY", ""),
                "app_name": "autogen-marketing-team"
            },
            "debug_mode": True
        }
    }
    
    # Initialiseer MCP server
    mcp_server = MCPServer(config["mcp"])
    await mcp_server.initialize()
    
    # Deploy naar Cloudflare
    if config["mcp"]["cloudflare"]["account_id"] and config["mcp"]["cloudflare"]["api_token"]:
        try:
            cloudflare_url = await deploy_to_cloudflare(config["mcp"]["cloudflare"])
            logger.info(f"Cloudflare deployment URL: {cloudflare_url}")
        except Exception as e:
            logger.error(f"Fout bij deployen naar Cloudflare: {str(e)}")
    else:
        logger.warning("Cloudflare credentials niet geconfigureerd, overslaan...")
    
    # Deploy naar Heroku
    if config["mcp"]["heroku"]["api_key"]:
        try:
            heroku_url = await deploy_to_heroku(config["mcp"]["heroku"])
            logger.info(f"Heroku deployment URL: {heroku_url}")
        except Exception as e:
            logger.error(f"Fout bij deployen naar Heroku: {str(e)}")
    else:
        logger.warning("Heroku credentials niet geconfigureerd, overslaan...")
    
    logger.info("Deployment voltooid")

if __name__ == "__main__":
    asyncio.run(main())