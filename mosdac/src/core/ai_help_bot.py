"""
Main AI Help Bot Orchestrator for MOSDAC
"""

import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from src.scrapers.mosdac_scraper import MOSDACScraper
from src.knowledge_graph.graph_manager import GraphManager
from src.nlp.query_processor import QueryProcessor, QueryIntent
from src.geospatial.spatial_processor import SpatialProcessor
from src.utils.logger import get_logger

class AIHelpBot:
    """Main AI Help Bot orchestrator"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        
        # Initialize components
        self.scraper = MOSDACScraper()
        self.graph_manager = GraphManager()
        self.query_processor = QueryProcessor()
        self.spatial_processor = SpatialProcessor()
        
        # Conversation history
        self.conversation_history = []
        
        self.logger.info("AI Help Bot initialized successfully")
        
    async def process_query(self, user_query: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a user query and generate response
        
        Args:
            user_query: User's query string
            user_context: Additional user context
            
        Returns:
            Dictionary containing response and metadata
        """
        try:
            start_time = datetime.now()
            
            # Add to conversation history
            self.conversation_history.append({
                'timestamp': start_time.isoformat(),
                'user_query': user_query,
                'user_context': user_context or {}
            })
            
            # Process the query
            query_analysis = self.query_processor.process_query(user_query)
            
            # Determine response strategy based on intent
            if query_analysis.intent == QueryIntent.GEOSPATIAL_QUERY:
                response = await self._handle_spatial_query(user_query, query_analysis)
            elif query_analysis.intent == QueryIntent.DATA_DOWNLOAD:
                response = await self._handle_data_download_query(user_query, query_analysis)
            elif query_analysis.intent == QueryIntent.API_HELP:
                response = await self._handle_api_query(user_query, query_analysis)
            elif query_analysis.intent == QueryIntent.TECHNICAL_SUPPORT:
                response = await self._handle_support_query(user_query, query_analysis)
            else:
                response = await self._handle_general_query(user_query, query_analysis)
                
            # Add response to conversation history
            self.conversation_history[-1]['response'] = response
            self.conversation_history[-1]['processing_time'] = (
                datetime.now() - start_time
            ).total_seconds()
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': "I'm sorry, I encountered an error while processing your query. Please try again.",
                'query_analysis': None,
                'sources': [],
                'suggestions': self._get_fallback_suggestions()
            }
            
    async def _handle_spatial_query(self, query: str, analysis) -> Dict[str, Any]:
        """Handle geospatial queries"""
        try:
            # Process spatial query
            spatial_result = self.spatial_processor.process_spatial_query(query)
            
            # Search knowledge graph for relevant content
            graph_results = self.graph_manager.search_content(query, limit=5)
            
            # Combine results
            response = {
                'success': True,
                'response_type': 'spatial',
                'query_analysis': {
                    'intent': analysis.intent.value,
                    'confidence': analysis.confidence,
                    'entities': {k.value: v for k, v in analysis.entities.items()}
                },
                'spatial_result': {
                    'query_type': spatial_result.query.query_type,
                    'results': spatial_result.results,
                    'metadata': spatial_result.metadata
                },
                'knowledge_graph_results': graph_results,
                'visualization': spatial_result.visualization,
                'sources': self._extract_sources(graph_results),
                'suggestions': self.spatial_processor.get_spatial_suggestions(query)
            }
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error handling spatial query: {e}")
            return self._create_error_response("spatial", str(e))
            
    async def _handle_data_download_query(self, query: str, analysis) -> Dict[str, Any]:
        """Handle data download queries"""
        try:
            # Search knowledge graph for data-related content
            graph_results = self.graph_manager.search_content(query, limit=10)
            
            # Look for download links and specifications
            download_info = self._extract_download_information(graph_results)
            
            response = {
                'success': True,
                'response_type': 'data_download',
                'query_analysis': {
                    'intent': analysis.intent.value,
                    'confidence': analysis.confidence,
                    'entities': {k.value: v for k, v in analysis.entities.items()}
                },
                'download_information': download_info,
                'knowledge_graph_results': graph_results,
                'sources': self._extract_sources(graph_results),
                'suggestions': [
                    "How do I access the data?",
                    "What file formats are available?",
                    "What is the data resolution?",
                    "How do I download large datasets?"
                ]
            }
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error handling data download query: {e}")
            return self._create_error_response("data_download", str(e))
            
    async def _handle_api_query(self, query: str, analysis) -> Dict[str, Any]:
        """Handle API-related queries"""
        try:
            # Search knowledge graph for API documentation
            api_query = f"API {query}"
            graph_results = self.graph_manager.search_content(api_query, limit=8)
            
            # Extract API-specific information
            api_info = self._extract_api_information(graph_results)
            
            response = {
                'success': True,
                'response_type': 'api_help',
                'query_analysis': {
                    'intent': analysis.intent.value,
                    'confidence': analysis.confidence,
                    'entities': {k.value: v for k, v in analysis.entities.items()}
                },
                'api_information': api_info,
                'knowledge_graph_results': graph_results,
                'sources': self._extract_sources(graph_results),
                'suggestions': [
                    "How do I authenticate with the API?",
                    "What are the rate limits?",
                    "How do I handle API errors?",
                    "What are the response formats?"
                ]
            }
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error handling API query: {e}")
            return self._create_error_response("api_help", str(e))
            
    async def _handle_support_query(self, query: str, analysis) -> Dict[str, Any]:
        """Handle technical support queries"""
        try:
            # Search knowledge graph for support content
            support_query = f"help support {query}"
            graph_results = self.graph_manager.search_content(support_query, limit=6)
            
            # Look for FAQ and support information
            support_info = self._extract_support_information(graph_results)
            
            response = {
                'success': True,
                'response_type': 'technical_support',
                'query_analysis': {
                    'intent': analysis.intent.value,
                    'confidence': analysis.confidence,
                    'entities': {k.value: v for k, v in analysis.entities.items()}
                },
                'support_information': support_info,
                'knowledge_graph_results': graph_results,
                'sources': self._extract_sources(graph_results),
                'suggestions': [
                    "How do I contact support?",
                    "What are common issues?",
                    "How do I report a bug?",
                    "Where can I find documentation?"
                ]
            }
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error handling support query: {e}")
            return self._create_error_response("technical_support", str(e))
            
    async def _handle_general_query(self, query: str, analysis) -> Dict[str, Any]:
        """Handle general information queries"""
        try:
            # Search knowledge graph
            graph_results = self.graph_manager.search_content(query, limit=8)
            
            # Generate general response
            response = {
                'success': True,
                'response_type': 'general',
                'query_analysis': {
                    'intent': analysis.intent.value,
                    'confidence': analysis.confidence,
                    'entities': {k.value: v for k, v in analysis.entities.items()}
                },
                'knowledge_graph_results': graph_results,
                'sources': self._extract_sources(graph_results),
                'suggestions': self.query_processor.get_query_suggestions(query)
            }
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error handling general query: {e}")
            return self._create_error_response("general", str(e))
            
    def _extract_download_information(self, graph_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract download-related information from graph results"""
        download_info = {
            'download_links': [],
            'file_formats': [],
            'data_specifications': [],
            'access_instructions': []
        }
        
        for result in graph_results:
            node_data = result.get('data', {})
            
            if node_data.get('type') == 'download_link':
                download_info['download_links'].append({
                    'url': node_data.get('url', ''),
                    'text': node_data.get('text', ''),
                    'file_type': node_data.get('file_type', '')
                })
            elif node_data.get('type') == 'specifications':
                download_info['data_specifications'].append(node_data.get('data', {}))
                
        return download_info
        
    def _extract_api_information(self, graph_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract API-related information from graph results"""
        api_info = {
            'documentation': [],
            'code_examples': [],
            'endpoints': [],
            'authentication': []
        }
        
        for result in graph_results:
            node_data = result.get('data', {})
            
            if node_data.get('type') == 'api_documentation':
                api_info['documentation'].append(node_data.get('text', ''))
            elif node_data.get('type') == 'code_example':
                api_info['code_examples'].append(node_data.get('code', ''))
                
        return api_info
        
    def _extract_support_information(self, graph_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract support-related information from graph results"""
        support_info = {
            'faqs': [],
            'troubleshooting': [],
            'contact_info': []
        }
        
        for result in graph_results:
            node_data = result.get('data', {})
            
            if node_data.get('type') == 'question':
                support_info['faqs'].append({
                    'question': node_data.get('text', ''),
                    'answer': self._find_answer_for_question(node_data.get('text', ''))
                })
                
        return support_info
        
    def _find_answer_for_question(self, question: str) -> str:
        """Find answer for a question in the knowledge graph"""
        # This is a simplified implementation
        # In a real system, you would query the graph for the answer
        return "Please refer to the MOSDAC documentation for detailed information."
        
    def _extract_sources(self, graph_results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Extract source information from graph results"""
        sources = []
        
        for result in graph_results:
            node_data = result.get('data', {})
            
            if 'url' in node_data:
                sources.append({
                    'url': node_data['url'],
                    'title': node_data.get('title', 'Unknown'),
                    'type': node_data.get('content_type', 'unknown')
                })
                
        return sources
        
    def _create_error_response(self, response_type: str, error_message: str) -> Dict[str, Any]:
        """Create error response"""
        return {
            'success': False,
            'response_type': response_type,
            'error': error_message,
            'response': f"I'm sorry, I couldn't process your request. Error: {error_message}",
            'sources': [],
            'suggestions': self._get_fallback_suggestions()
        }
        
    def _get_fallback_suggestions(self) -> List[str]:
        """Get fallback suggestions when errors occur"""
        return [
            "Try rephrasing your question",
            "Check the MOSDAC documentation",
            "Contact technical support",
            "Browse the FAQ section"
        ]
        
    async def scrape_and_update_knowledge(self, urls: List[str] = None) -> Dict[str, Any]:
        """
        Scrape MOSDAC content and update knowledge graph
        
        Args:
            urls: List of URLs to scrape (if None, discover content)
            
        Returns:
            Dictionary containing scraping results
        """
        try:
            if not urls:
                # Discover content from MOSDAC portal
                self.logger.info("Discovering content from MOSDAC portal...")
                urls = self.scraper.discover_content(
                    start_url="https://www.mosdac.gov.in",
                    max_depth=2
                )
                
            self.logger.info(f"Scraping {len(urls)} URLs...")
            
            # Scrape content
            scraped_content = self.scraper.scrape_multiple(urls)
            
            # Add to knowledge graph
            added_nodes = []
            for content in scraped_content:
                if content:
                    node_id = self.graph_manager.add_content(content)
                    added_nodes.append({
                        'url': content.get('url', ''),
                        'node_id': node_id,
                        'content_type': content.get('content_type', 'unknown')
                    })
                    
            # Get graph statistics
            graph_stats = self.graph_manager.get_graph_stats()
            
            return {
                'success': True,
                'urls_scraped': len(urls),
                'content_added': len(added_nodes),
                'added_nodes': added_nodes,
                'graph_statistics': graph_stats
            }
            
        except Exception as e:
            self.logger.error(f"Error in scraping and update: {e}")
            return {
                'success': False,
                'error': str(e),
                'urls_scraped': 0,
                'content_added': 0
            }
            
    def get_conversation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get conversation history
        
        Args:
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversation records
        """
        return self.conversation_history[-limit:] if self.conversation_history else []
        
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status and health information"""
        try:
            # Check component status
            components_status = {
                'scraper': 'active',
                'graph_manager': 'active' if self.graph_manager.nx_graph else 'inactive',
                'query_processor': 'active',
                'spatial_processor': 'active'
            }
            
            # Get graph statistics
            graph_stats = self.graph_manager.get_graph_stats()
            
            return {
                'status': 'healthy',
                'components': components_status,
                'knowledge_graph': graph_stats,
                'conversation_count': len(self.conversation_history),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'last_updated': datetime.now().isoformat()
            }
            
    def export_conversation_history(self, filepath: str):
        """Export conversation history to file"""
        try:
            with open(filepath, 'w') as f:
                json.dump(self.conversation_history, f, indent=2, default=str)
            self.logger.info(f"Conversation history exported to {filepath}")
        except Exception as e:
            self.logger.error(f"Error exporting conversation history: {e}")
            
    def clear_conversation_history(self):
        """Clear conversation history"""
        self.conversation_history.clear()
        self.logger.info("Conversation history cleared")
        
    def get_query_statistics(self) -> Dict[str, Any]:
        """Get query processing statistics"""
        if not self.conversation_history:
            return {}
            
        # Analyze conversation history
        total_queries = len(self.conversation_history)
        successful_queries = sum(1 for conv in self.conversation_history if conv.get('response', {}).get('success', False))
        
        # Intent distribution
        intent_counts = {}
        for conv in self.conversation_history:
            response = conv.get('response', {})
            if response.get('success'):
                intent = response.get('query_analysis', {}).get('intent', 'unknown')
                intent_counts[intent] = intent_counts.get(intent, 0) + 1
                
        # Average processing time
        processing_times = [conv.get('processing_time', 0) for conv in self.conversation_history if conv.get('processing_time')]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        return {
            'total_queries': total_queries,
            'successful_queries': successful_queries,
            'success_rate': successful_queries / total_queries if total_queries > 0 else 0,
            'intent_distribution': intent_counts,
            'average_processing_time': avg_processing_time,
            'total_processing_time': sum(processing_times)
        }
