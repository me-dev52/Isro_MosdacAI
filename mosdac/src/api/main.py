"""
FastAPI Backend for MOSDAC AI Help Bot
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from config.config import get_api_config
from src.core.ai_help_bot import AIHelpBot
from src.utils.logger import get_logger

# Initialize FastAPI app
app = FastAPI(
    title="MOSDAC AI Help Bot API",
    description="AI-based Help Bot for Information Retrieval from MOSDAC Portal",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
config = get_api_config()
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI Help Bot
ai_bot = AIHelpBot()
logger = get_logger(__name__)

# Pydantic models
class QueryRequest(BaseModel):
    query: str = Field(..., description="User query string")
    user_context: Optional[Dict[str, Any]] = Field(default=None, description="Additional user context")

class QueryResponse(BaseModel):
    success: bool
    response_type: str
    query_analysis: Optional[Dict[str, Any]] = None
    response: str
    sources: List[Dict[str, str]]
    suggestions: List[str]
    spatial_result: Optional[Dict[str, Any]] = None
    visualization: Optional[str] = None
    error: Optional[str] = None

class ScrapingRequest(BaseModel):
    urls: Optional[List[str]] = Field(default=None, description="Specific URLs to scrape")
    max_depth: int = Field(default=2, description="Maximum depth for content discovery")

class ScrapingResponse(BaseModel):
    success: bool
    urls_scraped: int
    content_added: int
    added_nodes: List[Dict[str, Any]]
    graph_statistics: Dict[str, Any]
    error: Optional[str] = None

class SystemStatus(BaseModel):
    status: str
    components: Dict[str, str]
    knowledge_graph: Dict[str, Any]
    conversation_count: int
    last_updated: str
    error: Optional[str] = None

class ConversationHistory(BaseModel):
    conversations: List[Dict[str, Any]]
    total_count: int

class QueryStatistics(BaseModel):
    total_queries: int
    successful_queries: int
    success_rate: float
    intent_distribution: Dict[str, int]
    average_processing_time: float
    total_processing_time: float

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "MOSDAC AI Help Bot API"
    }

# Main query endpoint
@app.post("/query", response_model=QueryResponse, tags=["Query"])
async def process_query(request: QueryRequest):
    """
    Process a user query and return AI-generated response
    
    This endpoint analyzes the user's query, determines the intent,
    searches the knowledge graph, and provides contextual responses
    with relevant sources and suggestions.
    """
    try:
        logger.info(f"Processing query: {request.query}")
        
        # Process query through AI Help Bot
        response = await ai_bot.process_query(request.query, request.user_context)
        
        return QueryResponse(**response)
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Scraping and knowledge update endpoint
@app.post("/scrape", response_model=ScrapingResponse, tags=["Knowledge Management"])
async def scrape_content(request: ScrapingRequest, background_tasks: BackgroundTasks):
    """
    Scrape MOSDAC content and update knowledge graph
    
    This endpoint can be used to:
    - Discover and scrape new content from the MOSDAC portal
    - Update the knowledge graph with fresh information
    - Process specific URLs if provided
    """
    try:
        logger.info("Starting content scraping process")
        
        # Run scraping in background
        result = await ai_bot.scrape_and_update_knowledge(request.urls)
        
        return ScrapingResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in scraping: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# System status endpoint
@app.get("/status", response_model=SystemStatus, tags=["System"])
async def get_system_status():
    """
    Get system status and health information
    
    Returns comprehensive system status including:
    - Component health status
    - Knowledge graph statistics
    - Conversation metrics
    - Last update timestamp
    """
    try:
        status = ai_bot.get_system_status()
        return SystemStatus(**status)
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Knowledge graph statistics endpoint
@app.get("/graph/stats", tags=["Knowledge Graph"])
async def get_graph_statistics():
    """
    Get knowledge graph statistics
    
    Returns detailed information about the knowledge graph including:
    - Total nodes and edges
    - Node type distribution
    - Edge type distribution
    """
    try:
        stats = ai_bot.graph_manager.get_graph_stats()
        return {
            "success": True,
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting graph statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Graph export endpoint
@app.get("/graph/export", tags=["Knowledge Graph"])
async def export_graph(
    format: str = Query("json", description="Export format (json, gml, graphml)")
):
    """
    Export knowledge graph to various formats
    
    Supported formats:
    - JSON: Human-readable format with all node and edge data
    - GML: Graph Modeling Language format
    - GraphML: XML-based graph format
    """
    try:
        if format not in ["json", "gml", "graphml"]:
            raise HTTPException(status_code=400, detail="Unsupported format")
            
        # Generate export filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mosdac_knowledge_graph_{timestamp}.{format}"
        filepath = f"data/{filename}"
        
        # Export graph
        ai_bot.graph_manager.export_graph(filepath, format)
        
        return {
            "success": True,
            "message": f"Graph exported to {filename}",
            "format": format,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error exporting graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Conversation history endpoint
@app.get("/conversations", response_model=ConversationHistory, tags=["Conversations"])
async def get_conversation_history(
    limit: int = Query(10, description="Maximum number of conversations to return")
):
    """
    Get conversation history
    
    Returns recent conversations with:
    - User queries and responses
    - Processing times
    - Query analysis results
    """
    try:
        conversations = ai_bot.get_conversation_history(limit)
        return ConversationHistory(
            conversations=conversations,
            total_count=len(conversations)
        )
        
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Query statistics endpoint
@app.get("/statistics", response_model=QueryStatistics, tags=["Analytics"])
async def get_query_statistics():
    """
    Get query processing statistics
    
    Returns comprehensive analytics including:
    - Query success rates
    - Intent distribution
    - Processing time metrics
    - Performance insights
    """
    try:
        stats = ai_bot.get_query_statistics()
        return QueryStatistics(**stats)
        
    except Exception as e:
        logger.error(f"Error getting query statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Clear conversation history endpoint
@app.delete("/conversations", tags=["Conversations"])
async def clear_conversation_history():
    """
    Clear conversation history
    
    Removes all stored conversation data.
    Use with caution as this action cannot be undone.
    """
    try:
        ai_bot.clear_conversation_history()
        return {
            "success": True,
            "message": "Conversation history cleared",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error clearing conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Export conversation history endpoint
@app.get("/conversations/export", tags=["Conversations"])
async def export_conversation_history():
    """
    Export conversation history to JSON file
    
    Downloads a JSON file containing all conversation data
    for backup or analysis purposes.
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversation_history_{timestamp}.json"
        filepath = f"data/{filename}"
        
        ai_bot.export_conversation_history(filepath)
        
        return {
            "success": True,
            "message": f"Conversation history exported to {filename}",
            "filename": filename,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error exporting conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Knowledge graph search endpoint
@app.get("/graph/search", tags=["Knowledge Graph"])
async def search_knowledge_graph(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, description="Maximum number of results")
):
    """
    Search the knowledge graph
    
    Performs semantic search across the knowledge graph
    to find relevant content based on the query.
    """
    try:
        results = ai_bot.graph_manager.search_content(query, limit)
        return {
            "success": True,
            "query": query,
            "results": results,
            "total_results": len(results),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error searching knowledge graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Related content endpoint
@app.get("/graph/related/{node_id}", tags=["Knowledge Graph"])
async def get_related_content(
    node_id: str,
    relationship_type: Optional[str] = Query(None, description="Type of relationship to follow")
):
    """
    Get related content for a specific node
    
    Returns content related to the specified node through
    various relationship types in the knowledge graph.
    """
    try:
        related = ai_bot.graph_manager.get_related_content(node_id, relationship_type)
        return {
            "success": True,
            "node_id": node_id,
            "related_content": related,
            "total_related": len(related),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting related content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Spatial query endpoint
@app.post("/spatial/query", tags=["Geospatial"])
async def process_spatial_query(request: QueryRequest):
    """
    Process a spatial query
    
    Handles geospatial queries and returns:
    - Spatial analysis results
    - Interactive map visualizations
    - Location-based information
    """
    try:
        logger.info(f"Processing spatial query: {request.query}")
        
        # Process through spatial processor
        spatial_result = ai_bot.spatial_processor.process_spatial_query(request.query)
        
        return {
            "success": True,
            "query": request.query,
            "spatial_result": {
                "query_type": spatial_result.query.query_type,
                "results": spatial_result.results,
                "metadata": spatial_result.metadata
            },
            "visualization": spatial_result.visualization,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing spatial query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Spatial suggestions endpoint
@app.get("/spatial/suggestions", tags=["Geospatial"])
async def get_spatial_suggestions(
    query: str = Query(..., description="Query to get suggestions for")
):
    """
    Get spatial query suggestions
    
    Returns relevant spatial query suggestions based on the input query.
    """
    try:
        suggestions = ai_bot.spatial_processor.get_spatial_suggestions(query)
        return {
            "success": True,
            "query": query,
            "suggestions": suggestions,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting spatial suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Root endpoint
@app.get("/", response_class=HTMLResponse, tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return """
    <html>
        <head>
            <title>MOSDAC AI Help Bot API</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 800px; margin: 0 auto; }
                .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
                .endpoints { margin-top: 30px; }
                .endpoint { background: #f9f9f9; padding: 15px; margin: 10px 0; border-radius: 3px; }
                .method { font-weight: bold; color: #0066cc; }
                .url { font-family: monospace; background: #e8e8e8; padding: 2px 6px; border-radius: 2px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 MOSDAC AI Help Bot API</h1>
                    <p>AI-based Help Bot for Information Retrieval from MOSDAC Portal</p>
                    <p><strong>Version:</strong> 1.0.0</p>
                    <p><strong>Status:</strong> <span style="color: green;">Active</span></p>
                </div>
                
                <div class="endpoints">
                    <h2>📚 API Endpoints</h2>
                    
                    <div class="endpoint">
                        <div class="method">POST</div>
                        <div class="url">/query</div>
                        <p>Process user queries and get AI-generated responses</p>
                    </div>
                    
                    <div class="endpoint">
                        <div class="method">POST</div>
                        <div class="url">/scrape</div>
                        <p>Scrape MOSDAC content and update knowledge graph</p>
                    </div>
                    
                    <div class="endpoint">
                        <div class="method">GET</div>
                        <div class="url">/status</div>
                        <p>Get system status and health information</p>
                    </div>
                    
                    <div class="endpoint">
                        <div class="method">GET</div>
                        <div class="url">/graph/stats</div>
                        <p>Get knowledge graph statistics</p>
                    </div>
                    
                    <div class="endpoint">
                        <div class="method">POST</div>
                        <div class="url">/spatial/query</div>
                        <p>Process geospatial queries</p>
                    </div>
                    
                    <div class="endpoint">
                        <div class="method">GET</div>
                        <div class="url">/conversations</div>
                        <p>Get conversation history</p>
                    </div>
                    
                    <div class="endpoint">
                        <div class="method">GET</div>
                        <div class="url">/statistics</div>
                        <p>Get query processing statistics</p>
                    </div>
                </div>
                
                <div style="margin-top: 30px; padding: 20px; background: #e8f4f8; border-radius: 5px;">
                    <h3>🔗 Quick Links</h3>
                    <ul>
                        <li><a href="/docs">📖 Interactive API Documentation</a></li>
                        <li><a href="/redoc">📋 Alternative API Documentation</a></li>
                        <li><a href="/health">💚 Health Check</a></li>
                    </ul>
                </div>
                
                <div style="margin-top: 30px; text-align: center; color: #666;">
                    <p>Built with ❤️ for MOSDAC Portal</p>
                    <p>Powered by AI/ML and Knowledge Graph Technology</p>
                </div>
            </div>
        </body>
    </html>
    """

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting MOSDAC AI Help Bot API...")
    
    # Initialize AI Help Bot
    global ai_bot
    ai_bot = AIHelpBot()
    
    logger.info("MOSDAC AI Help Bot API started successfully")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down MOSDAC AI Help Bot API...")
    
    # Cleanup resources
    if hasattr(ai_bot, 'scraper'):
        ai_bot.scraper.cleanup()
    
    logger.info("MOSDAC AI Help Bot API shutdown complete")

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=config.debug,
        log_level="info"
    )
