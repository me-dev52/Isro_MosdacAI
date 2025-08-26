"""
Knowledge Graph Manager for MOSDAC AI Help Bot
"""

import json
import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

import networkx as nx
from py2neo import Graph, Node, Relationship, NodeMatcher
from sentence_transformers import SentenceTransformer
import numpy as np

from config.config import get_database_config, get_model_config
from src.utils.logger import get_logger

class GraphManager:
    """Manages the knowledge graph for MOSDAC content"""
    
    def __init__(self):
        self.config = get_database_config()
        self.model_config = get_model_config()
        self.logger = get_logger(self.__class__.__name__)
        
        # Initialize Neo4j connection
        try:
            self.graph = Graph(
                self.config.neo4j_uri,
                auth=(self.config.neo4j_user, self.config.neo4j_password)
            )
            self.logger.info("Connected to Neo4j database")
        except Exception as e:
            self.logger.error(f"Failed to connect to Neo4j: {e}")
            self.graph = None
            
        # Initialize NetworkX for local graph operations
        self.nx_graph = nx.MultiDiGraph()
        
        # Initialize sentence transformer for embeddings
        try:
            self.embedding_model = SentenceTransformer(self.model_config.embedding_model)
            self.logger.info(f"Loaded embedding model: {self.model_config.embedding_model}")
        except Exception as e:
            self.logger.error(f"Failed to load embedding model: {e}")
            self.embedding_model = None
            
    def add_content(self, content_data: Dict[str, Any]) -> str:
        """
        Add content to the knowledge graph
        
        Args:
            content_data: Dictionary containing scraped content
            
        Returns:
            Node ID of the added content
        """
        try:
            if not self.graph:
                return self._add_to_local_graph(content_data)
                
            # Create content node
            content_node = Node(
                "Content",
                id=str(uuid.uuid4()),
                url=content_data.get('url', ''),
                content_type=content_data.get('content_type', 'unknown'),
                title=content_data.get('metadata', {}).get('title', ''),
                text_content=content_data.get('text_content', '')[:1000],  # Limit text length
                scraped_at=datetime.now().isoformat(),
                metadata=json.dumps(content_data.get('metadata', {}))
            )
            
            # Add to Neo4j
            tx = self.graph.begin()
            tx.create(content_node)
            tx.commit()
            
            # Add to local graph
            self._add_to_local_graph(content_data, content_node.identity)
            
            self.logger.info(f"Added content: {content_data.get('url', 'unknown')}")
            return str(content_node.identity)
            
        except Exception as e:
            self.logger.error(f"Error adding content: {e}")
            return self._add_to_local_graph(content_data)
            
    def _add_to_local_graph(self, content_data: Dict[str, Any], node_id: str = None) -> str:
        """Add content to local NetworkX graph"""
        if not node_id:
            node_id = str(uuid.uuid4())
            
        # Add content node
        self.nx_graph.add_node(
            node_id,
            type='content',
            url=content_data.get('url', ''),
            content_type=content_data.get('content_type', 'unknown'),
            title=content_data.get('metadata', {}).get('title', ''),
            text_content=content_data.get('text_content', ''),
            metadata=content_data.get('metadata', {})
        )
        
        # Process content based on type
        if content_data.get('content_type') == 'faq':
            self._process_faq_content(node_id, content_data)
        elif content_data.get('content_type') == 'data':
            self._process_data_content(node_id, content_data)
        elif content_data.get('content_type') == 'api':
            self._process_api_content(node_id, content_data)
            
        return node_id
        
    def _process_faq_content(self, content_node_id: str, content_data: Dict[str, Any]):
        """Process FAQ content and create question-answer relationships"""
        faqs = content_data.get('faqs', [])
        
        for faq in faqs:
            question_id = str(uuid.uuid4())
            answer_id = str(uuid.uuid4())
            
            # Add question node
            self.nx_graph.add_node(
                question_id,
                type='question',
                text=faq.get('question', ''),
                source_url=faq.get('source_url', ''),
                embedding=self._get_embedding(faq.get('question', ''))
            )
            
            # Add answer node
            self.nx_graph.add_node(
                answer_id,
                type='answer',
                text=faq.get('answer', ''),
                source_url=faq.get('source_url', ''),
                embedding=self._get_embedding(faq.get('answer', ''))
            )
            
            # Add relationships
            self.nx_graph.add_edge(content_node_id, question_id, type='contains')
            self.nx_graph.add_edge(question_id, answer_id, type='has_answer')
            
    def _process_data_content(self, content_node_id: str, content_data: Dict[str, Any]):
        """Process data content and create product relationships"""
        data_info = content_data.get('data_info', {})
        
        # Add product specifications
        if 'specifications' in data_info:
            specs_id = str(uuid.uuid4())
            self.nx_graph.add_node(
                specs_id,
                type='specifications',
                data=data_info['specifications']
            )
            self.nx_graph.add_edge(content_node_id, specs_id, type='has_specifications')
            
        # Add download links
        download_links = content_data.get('download_links', [])
        for link in download_links:
            link_id = str(uuid.uuid4())
            self.nx_graph.add_node(
                link_id,
                type='download_link',
                url=link.get('url', ''),
                text=link.get('text', ''),
                file_type=link.get('file_type', '')
            )
            self.nx_graph.add_edge(content_node_id, link_id, type='has_download')
            
    def _process_api_content(self, content_node_id: str, content_data: Dict[str, Any]):
        """Process API content and create service relationships"""
        api_info = content_data.get('api_info', {})
        
        # Add API documentation
        if 'documentation' in api_info:
            doc_id = str(uuid.uuid4())
            self.nx_graph.add_node(
                doc_id,
                type='api_documentation',
                text=api_info['documentation']
            )
            self.nx_graph.add_edge(content_node_id, doc_id, type='has_documentation')
            
        # Add code examples
        if 'code_examples' in api_info:
            code_id = str(uuid.uuid4())
            self.nx_graph.add_node(
                code_id,
                type='code_example',
                code=api_info['code_examples']
            )
            self.nx_graph.add_edge(content_node_id, code_id, type='has_example')
            
    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding for text"""
        if not self.embedding_model or not text:
            return None
            
        try:
            embedding = self.embedding_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            self.logger.error(f"Error generating embedding: {e}")
            return None
            
    def search_content(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search content using semantic similarity
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of search results
        """
        if not self.embedding_model:
            return self._text_search(query, limit)
            
        try:
            query_embedding = self.embedding_model.encode(query)
            
            # Search in local graph
            results = []
            for node_id, node_data in self.nx_graph.nodes(data=True):
                if 'embedding' in node_data and node_data['embedding']:
                    similarity = self._cosine_similarity(
                        query_embedding, 
                        node_data['embedding']
                    )
                    if similarity > 0.3:  # Threshold for relevance
                        results.append({
                            'node_id': node_id,
                            'similarity': similarity,
                            'data': node_data
                        })
                        
            # Sort by similarity and return top results
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:limit]
            
        except Exception as e:
            self.logger.error(f"Error in semantic search: {e}")
            return self._text_search(query, limit)
            
    def _text_search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Fallback text-based search"""
        query_lower = query.lower()
        results = []
        
        for node_id, node_data in self.nx_graph.nodes(data=True):
            score = 0
            
            # Check title
            if 'title' in node_data and query_lower in node_data['title'].lower():
                score += 2
                
            # Check text content
            if 'text_content' in node_data and query_lower in node_data['text_content'].lower():
                score += 1
                
            if score > 0:
                results.append({
                    'node_id': node_id,
                    'similarity': score / 3,  # Normalize score
                    'data': node_data
                })
                
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:limit]
        
    def _cosine_similarity(self, vec1: np.ndarray, vec2: List[float]) -> float:
        """Calculate cosine similarity between vectors"""
        try:
            vec2_array = np.array(vec2)
            dot_product = np.dot(vec1, vec2_array)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2_array)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
                
            return dot_product / (norm1 * norm2)
        except Exception:
            return 0.0
            
    def get_related_content(self, node_id: str, relationship_type: str = None) -> List[Dict[str, Any]]:
        """
        Get related content for a node
        
        Args:
            node_id: ID of the source node
            relationship_type: Type of relationship to follow
            
        Returns:
            List of related content
        """
        if not self.nx_graph.has_node(node_id):
            return []
            
        related = []
        
        if relationship_type:
            # Get specific relationship type
            for neighbor in self.nx_graph.neighbors(node_id):
                edge_data = self.nx_graph.get_edge_data(node_id, neighbor)
                if edge_data and any(edge.get('type') == relationship_type for edge in edge_data.values()):
                    related.append({
                        'node_id': neighbor,
                        'relationship': relationship_type,
                        'data': self.nx_graph.nodes[neighbor]
                    })
        else:
            # Get all neighbors
            for neighbor in self.nx_graph.neighbors(node_id):
                edge_data = self.nx_graph.get_edge_data(node_id, neighbor)
                for edge_key, edge_attrs in edge_data.items():
                    related.append({
                        'node_id': neighbor,
                        'relationship': edge_attrs.get('type', 'unknown'),
                        'data': self.nx_graph.nodes[neighbor]
                    })
                    
        return related
        
    def get_graph_stats(self) -> Dict[str, Any]:
        """Get knowledge graph statistics"""
        if not self.nx_graph:
            return {}
            
        stats = {
            'total_nodes': self.nx_graph.number_of_nodes(),
            'total_edges': self.nx_graph.number_of_edges(),
            'node_types': {},
            'edge_types': {}
        }
        
        # Count node types
        for node_data in self.nx_graph.nodes.values():
            node_type = node_data.get('type', 'unknown')
            stats['node_types'][node_type] = stats['node_types'].get(node_type, 0) + 1
            
        # Count edge types
        for edge_data in self.nx_graph.edges.values():
            edge_type = edge_data.get('type', 'unknown')
            stats['edge_types'][edge_type] = stats['edge_types'].get(edge_type, 0) + 1
            
        return stats
        
    def export_graph(self, filepath: str, format: str = 'json'):
        """
        Export knowledge graph to file
        
        Args:
            filepath: Path to export file
            format: Export format (json, gml, graphml)
        """
        try:
            if format == 'json':
                # Export as JSON
                graph_data = {
                    'nodes': [],
                    'edges': []
                }
                
                for node_id, node_data in self.nx_graph.nodes(data=True):
                    graph_data['nodes'].append({
                        'id': node_id,
                        **node_data
                    })
                    
                for source, target, edge_data in self.nx_graph.edges(data=True):
                    graph_data['edges'].append({
                        'source': source,
                        'target': target,
                        **edge_data
                    })
                    
                with open(filepath, 'w') as f:
                    json.dump(graph_data, f, indent=2)
                    
            elif format == 'gml':
                nx.write_gml(self.nx_graph, filepath)
            elif format == 'graphml':
                nx.write_graphml(self.nx_graph, filepath)
            else:
                raise ValueError(f"Unsupported format: {format}")
                
            self.logger.info(f"Exported graph to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error exporting graph: {e}")
            
    def clear_graph(self):
        """Clear the knowledge graph"""
        if self.graph:
            try:
                # Clear Neo4j
                tx = self.graph.begin()
                tx.run("MATCH (n) DETACH DELETE n")
                tx.commit()
                self.logger.info("Cleared Neo4j graph")
            except Exception as e:
                self.logger.error(f"Error clearing Neo4j: {e}")
                
        # Clear local graph
        self.nx_graph.clear()
        self.logger.info("Cleared local graph")
