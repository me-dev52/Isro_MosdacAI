#!/usr/bin/env python3
"""
Simple test script for MOSDAC AI Help Bot
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.core.ai_help_bot import AIHelpBot
from src.utils.logger import get_logger

async def test_bot():
    """Test the AI help bot with sample queries"""
    
    logger = get_logger("test_bot")
    logger.info("Starting AI Help Bot test...")
    
    try:
        # Initialize bot
        bot = AIHelpBot()
        logger.info("AI Help Bot initialized successfully")
        
        # Test queries
        test_queries = [
            "What satellite data is available for Mumbai region?",
            "How do I download satellite imagery?",
            "What is the spatial resolution of the data?",
            "How do I use the MOSDAC API?",
            "Show me data coverage for Delhi area"
        ]
        
        logger.info(f"Testing {len(test_queries)} queries...")
        
        for i, query in enumerate(test_queries, 1):
            logger.info(f"\n--- Test Query {i}: {query} ---")
            
            try:
                response = await bot.process_query(query)
                
                if response.get("success"):
                    logger.info("✅ Query processed successfully")
                    logger.info(f"Response Type: {response.get('response_type', 'Unknown')}")
                    
                    # Show query analysis
                    analysis = response.get("query_analysis", {})
                    if analysis:
                        logger.info(f"Intent: {analysis.get('intent', 'Unknown')}")
                        logger.info(f"Confidence: {analysis.get('confidence', 0):.2f}")
                        
                    # Show response
                    logger.info(f"Response: {response.get('response', 'No response')[:200]}...")
                    
                    # Show sources count
                    sources = response.get("sources", [])
                    logger.info(f"Sources: {len(sources)}")
                    
                    # Show suggestions count
                    suggestions = response.get("suggestions", [])
                    logger.info(f"Suggestions: {len(suggestions)}")
                    
                else:
                    logger.error(f"❌ Query failed: {response.get('error', 'Unknown error')}")
                    
            except Exception as e:
                logger.error(f"❌ Error processing query: {e}")
                
        # Test system status
        logger.info("\n--- Testing System Status ---")
        try:
            status = bot.get_system_status()
            logger.info(f"System Status: {status.get('status', 'Unknown')}")
            
            components = status.get("components", {})
            for component, comp_status in components.items():
                logger.info(f"  {component}: {comp_status}")
                
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            
        # Test knowledge graph stats
        logger.info("\n--- Testing Knowledge Graph ---")
        try:
            stats = bot.graph_manager.get_graph_stats()
            logger.info(f"Graph Nodes: {stats.get('total_nodes', 0)}")
            logger.info(f"Graph Edges: {stats.get('total_edges', 0)}")
            
        except Exception as e:
            logger.error(f"Error getting graph stats: {e}")
            
        logger.info("\n✅ Test completed!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False
        
    return True

def test_spatial_processor():
    """Test spatial processor functionality"""
    
    logger = get_logger("test_spatial")
    logger.info("Testing Spatial Processor...")
    
    try:
        from src.geospatial.spatial_processor import SpatialProcessor
        
        processor = SpatialProcessor()
        
        # Test spatial queries
        test_spatial_queries = [
            "Show satellite data for Mumbai region",
            "What data is available around Delhi?",
            "Show coverage within 50km of Bangalore"
        ]
        
        for query in test_spatial_queries:
            logger.info(f"\n--- Testing Spatial Query: {query} ---")
            
            try:
                result = processor.process_spatial_query(query)
                
                if result.query.query_type != "unknown":
                    logger.info(f"✅ Query Type: {result.query.query_type}")
                    logger.info(f"Results: {len(result.results)}")
                    
                    # Show first result
                    if result.results:
                        first_result = result.results[0]
                        logger.info(f"First Result Type: {first_result.get('type', 'Unknown')}")
                        
                else:
                    logger.warning("⚠️ Could not parse spatial query")
                    
            except Exception as e:
                logger.error(f"❌ Error processing spatial query: {e}")
                
        logger.info("✅ Spatial processor test completed!")
        
    except Exception as e:
        logger.error(f"❌ Spatial processor test failed: {e}")

def test_query_processor():
    """Test query processor functionality"""
    
    logger = get_logger("test_query")
    logger.info("Testing Query Processor...")
    
    try:
        from src.nlp.query_processor import QueryProcessor
        
        processor = QueryProcessor()
        
        # Test queries
        test_queries = [
            "What satellite data is available?",
            "How do I download data?",
            "Show me data for Mumbai",
            "API documentation please"
        ]
        
        for query in test_queries:
            logger.info(f"\n--- Testing Query: {query} ---")
            
            try:
                analysis = processor.process_query(query)
                
                logger.info(f"✅ Intent: {analysis.intent.value}")
                logger.info(f"Confidence: {analysis.confidence:.2f}")
                logger.info(f"Keywords: {analysis.keywords}")
                
                # Show entities
                if analysis.entities:
                    logger.info("Entities found:")
                    for entity_type, values in analysis.entities.items():
                        logger.info(f"  {entity_type.value}: {values}")
                        
            except Exception as e:
                logger.error(f"❌ Error processing query: {e}")
                
        logger.info("✅ Query processor test completed!")
        
    except Exception as e:
        logger.error(f"❌ Query processor test failed: {e}")

async def main():
    """Main test function"""
    
    print("🚀 MOSDAC AI Help Bot - Test Suite")
    print("=" * 50)
    
    # Test individual components
    print("\n1. Testing Query Processor...")
    test_query_processor()
    
    print("\n2. Testing Spatial Processor...")
    test_spatial_processor()
    
    print("\n3. Testing Full AI Help Bot...")
    success = await test_bot()
    
    if success:
        print("\n🎉 All tests completed successfully!")
    else:
        print("\n❌ Some tests failed!")
        
    print("\n" + "=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
