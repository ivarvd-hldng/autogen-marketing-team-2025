// Cloudflare Worker script voor AutoGen Marketing Team

import { Router } from 'itty-router';
import { Toucan } from 'toucan-js';

// Maak een nieuwe router
const router = Router();

// Error reporting setup
const setupSentry = (request, env) => {
  return new Toucan({
    dsn: env.SENTRY_DSN || '',
    context: { request },
    allowedHeaders: ['user-agent'],
    allowedSearchParams: /(.*)/,
    debug: env.DEBUG === 'true',
  });
};

// Middleware voor authenticatie
const authenticate = async (request, env) => {
  const authHeader = request.headers.get('Authorization');
  
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return new Response(JSON.stringify({
      status: 'error',
      error: {
        code: 'authentication_failed',
        message: 'API key is missing or invalid'
      }
    }), {
      status: 401,
      headers: {
        'Content-Type': 'application/json'
      }
    });
  }
  
  const apiKey = authHeader.replace('Bearer ', '');
  
  // Haal geldige API keys op uit de KV store
  const validKeys = await env.AGENT_DATA.get('api_keys', { type: 'json' }) || ["test_key"];
  
  if (!validKeys.includes(apiKey)) {
    return new Response(JSON.stringify({
      status: 'error',
      error: {
        code: 'authentication_failed',
        message: 'API key is invalid'
      }
    }), {
      status: 401,
      headers: {
        'Content-Type': 'application/json'
      }
    });
  }
};

// Middleware voor rate limiting
const rateLimit = async (request, env) => {
  const clientIP = request.headers.get('CF-Connecting-IP');
  const rateLimitKey = `ratelimit:${clientIP}`;
  
  // Haal huidige rate limit data op
  const rateLimitData = await env.AGENT_DATA.get(rateLimitKey, { type: 'json' }) || {
    count: 0,
    timestamp: Date.now()
  };
  
  // Reset als het meer dan een minuut geleden is
  const now = Date.now();
  if (now - rateLimitData.timestamp > 60000) {
    rateLimitData.count = 0;
    rateLimitData.timestamp = now;
  }
  
  // Verhoog teller
  rateLimitData.count += 1;
  
  // Controleer limiet (10 verzoeken per minuut)
  if (rateLimitData.count > 10) {
    return new Response(JSON.stringify({
      status: 'error',
      error: {
        code: 'rate_limit_exceeded',
        message: 'Rate limit exceeded for requests per minute'
      }
    }), {
      status: 429,
      headers: {
        'Content-Type': 'application/json'
      }
    });
  }
  
  // Sla nieuwe data op
  await env.AGENT_DATA.put(rateLimitKey, JSON.stringify(rateLimitData));
};

// Middleware voor CORS
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
};

// Middleware voor het toevoegen van CORS headers
const handleCors = request => {
  if (request.method === 'OPTIONS') {
    return new Response(null, {
      headers: corsHeaders
    });
  }
};

// Routes
router.get('/', () => {
  return new Response(JSON.stringify({
    status: 'online',
    message: 'AutoGen Marketing Team API'
  }), {
    headers: {
      'Content-Type': 'application/json',
      ...corsHeaders
    }
  });
});

router.get('/api/status', async (request, env) => {
  // Authenticatie check
  const authResponse = await authenticate(request, env);
  if (authResponse) return authResponse;
  
  // Rate limit check
  const rateLimitResponse = await rateLimit(request, env);
  if (rateLimitResponse) return rateLimitResponse;
  
  // Haal agent status op uit Durable Object
  const id = env.AGENT_SESSIONS.idFromName('system_status');
  const agentStateStore = env.AGENT_SESSIONS.get(id);
  const status = await agentStateStore.fetch('/status').then(res => res.json());
  
  return new Response(JSON.stringify({
    status: 'online',
    version: '1.0.0',
    agents: status.agents,
    uptime: status.uptime,
    requests_processed: status.requests_processed,
    timestamp: new Date().toISOString()
  }), {
    headers: {
      'Content-Type': 'application/json',
      ...corsHeaders
    }
  });
});

router.post('/api/generate', async (request, env) => {
  // Authenticatie check
  const authResponse = await authenticate(request, env);
  if (authResponse) return authResponse;
  
  // Rate limit check
  const rateLimitResponse = await rateLimit(request, env);
  if (rateLimitResponse) return rateLimitResponse;
  
  try {
    // Parse request body
    const body = await request.json();
    
    // Valideer input
    const { prompt, campaign_type, brand_info, target_audience } = body;
    if (!prompt || !campaign_type || !brand_info || !target_audience) {
      return new Response(JSON.stringify({
        status: 'error',
        error: {
          code: 'invalid_parameters',
          message: 'Missing required fields',
          details: {
            missing_fields: [
              !prompt ? 'prompt' : null,
              !campaign_type ? 'campaign_type' : null,
              !brand_info ? 'brand_info' : null,
              !target_audience ? 'target_audience' : null
            ].filter(Boolean)
          }
        }
      }), {
        status: 400,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        }
      });
    }
    
    // Genereer unieke request ID
    const requestId = crypto.randomUUID();
    
    // Maak een content creator session in de Durable Object
    const creatorId = env.AGENT_SESSIONS.idFromName(`creator_${requestId}`);
    const contentCreator = env.AGENT_SESSIONS.get(creatorId);
    
    // Stuur request naar content creator
    const creatorResponse = await contentCreator.fetch('/create', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        prompt,
        campaign_type,
        brand_info,
        target_audience
      })
    }).then(res => res.json());
    
    // Stuur de originele content naar de reviewer
    const reviewerId = env.AGENT_SESSIONS.idFromName(`reviewer_${requestId}`);
    const marketingReviewer = env.AGENT_SESSIONS.get(reviewerId);
    
    // Stuur request naar marketing reviewer
    const reviewerResponse = await marketingReviewer.fetch('/review', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        content: creatorResponse.content,
        campaign_type,
        brand_info,
        target_audience
      })
    }).then(res => res.json());
    
    // Combineer resultaten
    const results = {
      original_content: creatorResponse.content,
      review: reviewerResponse.review,
      score: reviewerResponse.score,
      improved_content: reviewerResponse.improved_content,
      campaign_type,
      timestamp: new Date().toISOString()
    };
    
    // Sla resultaten op in KV store
    await env.AGENT_DATA.put(
      `results:${requestId}`,
      JSON.stringify(results),
      { expirationTtl: 60 * 60 * 24 * 7 } // 1 week
    );
    
    return new Response(JSON.stringify({
      request_id: requestId,
      status: 'success',
      data: results
    }), {
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  } catch (error) {
    // Log error naar Sentry als het beschikbaar is
    const sentry = setupSentry(request, env);
    sentry.captureException(error);
    
    return new Response(JSON.stringify({
      status: 'error',
      error: {
        code: 'internal_error',
        message: 'Error generating content',
        details: error.message
      }
    }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders
      }
    });
  }
});

// Durable Object voor agent state management
export class AgentStateStore {
  constructor(state, env) {
    this.state = state;
    this.env = env;
    this.storage = state.storage;
    this.sessions = {};
    this.claude = env.CLAUDE;
  }
  
  async fetch(request) {
    const url = new URL(request.url);
    const path = url.pathname;
    
    // Status endpoint
    if (path === '/status') {
      return new Response(JSON.stringify({
        agents: {
          content_creator: 'active',
          marketing_reviewer: 'active'
        },
        uptime: Date.now() - (await this.storage.get('start_time') || Date.now()),
        requests_processed: await this.storage.get('requests_processed') || 0
      }), {
        headers: {
          'Content-Type': 'application/json'
        }
      });
    }
    
    // Content creator endpoint
    if (path === '/create') {
      if (request.method !== 'POST') {
        return new Response('Method not allowed', { status: 405 });
      }
      
      const { prompt, campaign_type, brand_info, target_audience } = await request.json();
      
      // Gebruik Claude voor content generatie
      const systemPrompt = `Je bent ContentCreator, een ervaren marketing professional gespecialiseerd in het schrijven van overtuigende en boeiende marketingcontent. 
      Je taak is om originele marketingcontent te creëren op basis van merk- en campagneinformatie.
      Je bent creatief, strategisch en begrijpt hoe je content kunt afstemmen op verschillende doelgroepen en kanalen.
      Je houdt rekening met de merkidentiteit en campagnedoelen bij het creëren van content.`;
      
      const userPrompt = `Creëer ${campaign_type} content voor het volgende merk:
      
      MERK INFORMATIE:
      ${brand_info}
      
      DOELGROEP:
      ${target_audience}
      
      VERZOEK:
      ${prompt}
      
      Zorg dat de content perfect is afgestemd op de merkidentiteit en doelgroep.
      Maak het overtuigend, boeiend en geschikt voor het specifieke kanaal (${campaign_type}).`;
      
      try {
        const response = await this.claude.sendMessage({
          system: systemPrompt,
          messages: [{ role: 'user', content: userPrompt }],
          temperature: 0.7,
          max_tokens: 2000
        });
        
        // Verhoog de teller voor verwerkte requests
        const requestsProcessed = (await this.storage.get('requests_processed') || 0) + 1;
        await this.storage.put('requests_processed', requestsProcessed);
        
        return new Response(JSON.stringify({
          content: response.content[0].text
        }), {
          headers: {
            'Content-Type': 'application/json'
          }
        });
      } catch (error) {
        return new Response(JSON.stringify({
          error: error.message
        }), {
          status: 500,
          headers: {
            'Content-Type': 'application/json'
          }
        });
      }
    }
    
    // Marketing reviewer endpoint
    if (path === '/review') {
      if (request.method !== 'POST') {
        return new Response('Method not allowed', { status: 405 });
      }
      
      const { content, campaign_type, brand_info, target_audience } = await request.json();
      
      // Gebruik Claude voor content review
      const systemPrompt = `Je bent MarketingReviewer, een marketing expert gespecialiseerd in het beoordelen en verbeteren van marketingcontent. 
      Je taak is om marketingcontent kritisch te beoordelen en concrete verbeteringen voor te stellen.
      Je hebt expertise in copywriting, branding, marketingstrategie en doelgroepanalyse.
      Je beoordeelt content op effectiviteit, merkwaarden, tone of voice, en conversiedoelen.`;
      
      const userPrompt = `Beoordeel en verbeter de volgende ${campaign_type} content:
      
      CONTENT:
      ${content}
      
      MERK INFORMATIE:
      ${brand_info}
      
      DOELGROEP:
      ${target_audience}
      
      Geef een gestructureerde beoordeling met:
      1. Algemene indruk (schaal 1-10)
      2. Sterke punten
      3. Verbeterpunten
      4. Verbeterde versie van de content
      5. Uitleg van de wijzigingen
      
      Zorg dat de verbeterde content perfect aansluit bij de merkidentiteit en doelgroep.`;
      
      try {
        const response = await this.claude.sendMessage({
          system: systemPrompt,
          messages: [{ role: 'user', content: userPrompt }],
          temperature: 0.3,
          max_tokens: 2000
        });
        
        const result = response.content[0].text;
        
        // Parse de resultaten (vereenvoudigd)
        const sections = result.split('\n\n');
        
        // Probeer de score te extraheren
        let score = 0;
        const scoreLineIndex = sections.findIndex(s => s.toLowerCase().includes('algemene indruk') || s.toLowerCase().includes('schaal'));
        if (scoreLineIndex >= 0) {
          const scoreLine = sections[scoreLineIndex];
          const scoreMatch = scoreLine.match(/\d+/);
          if (scoreMatch) {
            score = parseInt(scoreMatch[0], 10);
          }
        }
        
        // Zoek verbeterde content
        let improvedContent = '';
        const improvedContentHeaderIndex = sections.findIndex(s => 
          s.toLowerCase().includes('verbeterde versie') || 
          s.toLowerCase().includes('verbeterde content'));
        
        if (improvedContentHeaderIndex >= 0 && improvedContentHeaderIndex + 1 < sections.length) {
          improvedContent = sections[improvedContentHeaderIndex + 1];
        }
        
        // Verhoog de teller voor verwerkte requests
        const requestsProcessed = (await this.storage.get('requests_processed') || 0) + 1;
        await this.storage.put('requests_processed', requestsProcessed);
        
        return new Response(JSON.stringify({
          review: result,
          score,
          improved_content: improvedContent
        }), {
          headers: {
            'Content-Type': 'application/json'
          }
        });
      } catch (error) {
        return new Response(JSON.stringify({
          error: error.message
        }), {
          status: 500,
          headers: {
            'Content-Type': 'application/json'
          }
        });
      }
    }
    
    return new Response('Not found', { status: 404 });
  }
}

// Websocket handler voor real-time agent communicatie
async function handleWebsocket(request, env) {
  // Alleen WebSocket requests accepteren
  if (request.headers.get('Upgrade') !== 'websocket') {
    return new Response('Expected WebSocket', { status: 400 });
  }
  
  // Accepteer de WebSocket verbinding
  const pair = new WebSocketPair();
  const [client, server] = Object.values(pair);
  
  // Accepteer de verbinding
  server.accept();
  
  // Event handlers voor de WebSocket
  server.addEventListener('message', async event => {
    try {
      const data = JSON.parse(event.data);
      
      // Authenticatie bericht verwachten
      if (data.type === 'auth') {
        const apiKey = data.api_key;
        
        // Valideer API key
        const validKeys = await env.AGENT_DATA.get('api_keys', { type: 'json' }) || ["test_key"];
        
        if (!validKeys.includes(apiKey)) {
          server.send(JSON.stringify({
            type: 'error',
            message: 'Invalid API key',
            code: 'authentication_failed'
          }));
          server.close(1008, 'Authentication failed');
          return;
        }
        
        // Stuur bevestiging
        server.send(JSON.stringify({
          type: 'connection_established',
          timestamp: new Date().toISOString()
        }));
      }
      // Content generatie request
      else if (data.type === 'generate') {
        const { prompt, campaign_type, brand_info, target_audience } = data.data || {};
        
        if (!prompt || !campaign_type || !brand_info || !target_audience) {
          server.send(JSON.stringify({
            type: 'error',
            message: 'Missing required fields',
            code: 'invalid_parameters'
          }));
          return;
        }
        
        // Stuur statusupdate
        server.send(JSON.stringify({
          type: 'agent_message',
          agent: 'content_creator',
          message: `Ik ga nu content creëren voor een ${campaign_type}`,
          timestamp: new Date().toISOString()
        }));
        
        // Content creator request
        const requestId = crypto.randomUUID();
        const creatorId = env.AGENT_SESSIONS.idFromName(`creator_${requestId}`);
        const contentCreator = env.AGENT_SESSIONS.get(creatorId);
        
        const creatorResponse = await contentCreator.fetch('/create', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            prompt,
            campaign_type,
            brand_info,
            target_audience
          })
        }).then(res => res.json());
        
        // Stuur originele content
        server.send(JSON.stringify({
          type: 'content',
          content: creatorResponse.content,
          timestamp: new Date().toISOString()
        }));
        
        // Stuur statusupdate voor reviewer
        server.send(JSON.stringify({
          type: 'agent_message',
          agent: 'marketing_reviewer',
          message: 'Ik ga nu de gegenereerde content beoordelen',
          timestamp: new Date().toISOString()
        }));
        
        // Marketing reviewer request
        const reviewerId = env.AGENT_SESSIONS.idFromName(`reviewer_${requestId}`);
        const marketingReviewer = env.AGENT_SESSIONS.get(reviewerId);
        
        const reviewerResponse = await marketingReviewer.fetch('/review', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            content: creatorResponse.content,
            campaign_type,
            brand_info,
            target_audience
          })
        }).then(res => res.json());
        
        // Stuur review resultaten
        server.send(JSON.stringify({
          type: 'review',
          review: reviewerResponse.review,
          score: reviewerResponse.score,
          improved_content: reviewerResponse.improved_content,
          timestamp: new Date().toISOString()
        }));
        
        // Stuur voltooiingsbericht
        server.send(JSON.stringify({
          type: 'complete',
          request_id: requestId,
          timestamp: new Date().toISOString()
        }));
      }
      // Ping-pong voor keep-alive
      else if (data.type === 'ping') {
        server.send(JSON.stringify({
          type: 'pong',
          timestamp: new Date().toISOString()
        }));
      }
    } catch (error) {
      // Stuur foutbericht
      server.send(JSON.stringify({
        type: 'error',
        message: 'Error processing message',
        details: error.message
      }));
    }
  });
  
  // Error event handler
  server.addEventListener('error', err => {
    console.error('WebSocket error:', err);
  });
  
  // Close event handler
  server.addEventListener('close', () => {
    console.log('WebSocket closed');
  });
  
  return new Response(null, {
    status: 101,
    webSocket: client
  });
}

// WebSocket endpoint
router.get('/ws', async (request, env) => {
  return handleWebsocket(request, env);
});

// 404 handler
router.all('*', () => new Response('Not Found', { status: 404 }));

// Verwerk alle requests met de router
export default {
  async fetch(request, env, ctx) {
    // Controleer eerst op CORS preflight requests
    const corsResponse = handleCors(request);
    if (corsResponse) return corsResponse;
    
    // Sla start tijd op als die nog niet bestaat
    if (!await env.AGENT_DATA.get('start_time')) {
      await env.AGENT_DATA.put('start_time', Date.now());
    }
    
    return router.handle(request, env, ctx);
  }
};