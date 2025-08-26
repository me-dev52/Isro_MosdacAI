"""
NLP Query Processor for MOSDAC AI Help Bot
"""

import re
import spacy
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from config.config import get_model_config, get_openai_config
from src.utils.logger import get_logger

class QueryIntent(Enum):
    """Query intent classification"""
    INFORMATION_RETRIEVAL = "information_retrieval"
    DATA_DOWNLOAD = "data_download"
    TECHNICAL_SUPPORT = "technical_support"
    GEOSPATIAL_QUERY = "geospatial_query"
    API_HELP = "api_help"
    GENERAL_QUESTION = "general_question"
    UNKNOWN = "unknown"

class QueryEntity(Enum):
    """Query entity types"""
    LOCATION = "location"
    SATELLITE = "satellite"
    SENSOR = "sensor"
    DATA_TYPE = "data_type"
    TIME_PERIOD = "time_period"
    RESOLUTION = "resolution"
    FILE_FORMAT = "file_format"
    API_ENDPOINT = "api_endpoint"

@dataclass
class QueryAnalysis:
    """Query analysis result"""
    intent: QueryIntent
    entities: Dict[QueryEntity, List[str]]
    confidence: float
    keywords: List[str]
    original_query: str
    processed_query: str

class QueryProcessor:
    """Processes and analyzes user queries"""
    
    def __init__(self):
        self.config = get_model_config()
        self.openai_config = get_openai_config()
        self.logger = get_logger(self.__class__.__name__)
        
        # Load spaCy model
        try:
            self.nlp = spacy.load(self.config.spacy_model)
            self.logger.info(f"Loaded spaCy model: {self.config.spacy_model}")
        except OSError:
            self.logger.warning(f"spaCy model {self.config.spacy_model} not found. Downloading...")
            try:
                import subprocess
                subprocess.run([
                    "python", "-m", "spacy", "download", self.config.spacy_model
                ], check=True)
                self.nlp = spacy.load(self.config.spacy_model)
                self.logger.info(f"Downloaded and loaded spaCy model: {self.config.spacy_model}")
            except Exception as e:
                self.logger.error(f"Failed to load spaCy model: {e}")
                self.nlp = None
                
        # Initialize patterns
        self._init_patterns()
        
    def _init_patterns(self):
        """Initialize regex patterns for entity extraction"""
        # Location patterns
        self.location_patterns = [
            r'\b(?:in|at|near|around|within)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:region|area|zone|city|state)',
            r'\b(?:latitude|longitude|coordinates?)\s+(?:of|for)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        ]
        
        # Satellite patterns
        self.satellite_patterns = [
            r'\b(?:satellite|mission)\s+(?:data|imagery|information)\s+(?:from|of)\s+([A-Z0-9\-]+)',
            r'\b([A-Z0-9\-]+)\s+(?:satellite|mission|data)',
            r'\b(?:data|imagery)\s+(?:from|of)\s+([A-Z0-9\-]+)'
        ]
        
        # Sensor patterns
        self.sensor_patterns = [
            r'\b(?:sensor|instrument)\s+(?:data|information)\s+(?:from|of)\s+([A-Z0-9\-]+)',
            r'\b([A-Z0-9\-]+)\s+(?:sensor|instrument)',
            r'\b(?:data|information)\s+(?:from|of)\s+([A-Z0-9\-]+)\s+(?:sensor|instrument)'
        ]
        
        # Data type patterns
        self.data_type_patterns = [
            r'\b(?:data|product|information)\s+(?:type|format)\s+(?:of|for)\s+([A-Za-z0-9\s\-]+)',
            r'\b([A-Za-z0-9\s\-]+)\s+(?:data|product|information)',
            r'\b(?:satellite|remote\s+sensing)\s+([A-Za-z0-9\s\-]+)'
        ]
        
        # Time period patterns
        self.time_patterns = [
            r'\b(?:data|information|imagery)\s+(?:from|for|between)\s+([A-Za-z0-9\s\-]+)',
            r'\b(?:temporal|time)\s+(?:coverage|resolution|period)\s+(?:of|for)\s+([A-Za-z0-9\s\-]+)',
            r'\b(?:historical|recent|latest|archived)\s+([A-Za-z0-9\s\-]+)'
        ]
        
        # Resolution patterns
        self.resolution_patterns = [
            r'\b(?:spatial|ground)\s+resolution\s+(?:of|for)\s+([0-9\.]+\s*(?:m|km|meters?|kilometers?))',
            r'\b([0-9\.]+\s*(?:m|km|meters?|kilometers?))\s+(?:resolution|pixel\s+size)',
            r'\b(?:high|low|medium)\s+resolution\s+([A-Za-z0-9\s\-]+)'
        ]
        
        # File format patterns
        self.file_format_patterns = [
            r'\b(?:file|data)\s+format\s+(?:of|for)\s+([A-Za-z0-9]+)',
            r'\b([A-Za-z0-9]+)\s+(?:file|data)\s+format',
            r'\b(?:download|export)\s+(?:as|in)\s+([A-Za-z0-9]+)'
        ]
        
        # API patterns
        self.api_patterns = [
            r'\b(?:API|endpoint|service)\s+(?:for|to|of)\s+([A-Za-z0-9\s\-]+)',
            r'\b(?:how\s+to|how\s+do\s+I)\s+(?:use|access|call)\s+([A-Za-z0-9\s\-]+)\s+(?:API|service)',
            r'\b(?:API|service)\s+(?:documentation|help|example)\s+(?:for|of)\s+([A-Za-z0-9\s\-]+)'
        ]
        
    def process_query(self, query: str) -> QueryAnalysis:
        """
        Process and analyze a user query
        
        Args:
            query: User's query string
            
        Returns:
            QueryAnalysis object containing analysis results
        """
        try:
            # Clean and normalize query
            processed_query = self._preprocess_query(query)
            
            # Extract entities
            entities = self._extract_entities(processed_query)
            
            # Classify intent
            intent, confidence = self._classify_intent(processed_query, entities)
            
            # Extract keywords
            keywords = self._extract_keywords(processed_query)
            
            return QueryAnalysis(
                intent=intent,
                entities=entities,
                confidence=confidence,
                keywords=keywords,
                original_query=query,
                processed_query=processed_query
            )
            
        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            return QueryAnalysis(
                intent=QueryIntent.UNKNOWN,
                entities={},
                confidence=0.0,
                keywords=[],
                original_query=query,
                processed_query=query
            )
            
    def _preprocess_query(self, query: str) -> str:
        """
        Preprocess and normalize query
        
        Args:
            query: Raw query string
            
        Returns:
            Preprocessed query string
        """
        # Convert to lowercase
        query = query.lower()
        
        # Remove extra whitespace
        query = re.sub(r'\s+', ' ', query).strip()
        
        # Remove punctuation (keep some for entity extraction)
        query = re.sub(r'[^\w\s\-\.]', ' ', query)
        
        # Normalize whitespace
        query = re.sub(r'\s+', ' ', query).strip()
        
        return query
        
    def _extract_entities(self, query: str) -> Dict[QueryEntity, List[str]]:
        """
        Extract entities from query using regex patterns and spaCy
        
        Args:
            query: Preprocessed query string
            
        Returns:
            Dictionary mapping entity types to extracted values
        """
        entities = {}
        
        # Extract using regex patterns
        entities.update(self._extract_with_patterns(query))
        
        # Extract using spaCy if available
        if self.nlp:
            entities.update(self._extract_with_spacy(query))
            
        return entities
        
    def _extract_with_patterns(self, query: str) -> Dict[QueryEntity, List[str]]:
        """Extract entities using regex patterns"""
        entities = {}
        
        # Location extraction
        locations = []
        for pattern in self.location_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            locations.extend(matches)
        if locations:
            entities[QueryEntity.LOCATION] = list(set(locations))
            
        # Satellite extraction
        satellites = []
        for pattern in self.satellite_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            satellites.extend(matches)
        if satellites:
            entities[QueryEntity.SATELLITE] = list(set(satellites))
            
        # Sensor extraction
        sensors = []
        for pattern in self.sensor_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            sensors.extend(matches)
        if sensors:
            entities[QueryEntity.SENSOR] = list(set(sensors))
            
        # Data type extraction
        data_types = []
        for pattern in self.data_type_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            data_types.extend(matches)
        if data_types:
            entities[QueryEntity.DATA_TYPE] = list(set(data_types))
            
        # Time period extraction
        time_periods = []
        for pattern in self.time_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            time_periods.extend(matches)
        if time_periods:
            entities[QueryEntity.TIME_PERIOD] = list(set(time_periods))
            
        # Resolution extraction
        resolutions = []
        for pattern in self.resolution_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            resolutions.extend(matches)
        if resolutions:
            entities[QueryEntity.RESOLUTION] = list(set(resolutions))
            
        # File format extraction
        file_formats = []
        for pattern in self.file_format_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            file_formats.extend(matches)
        if file_formats:
            entities[QueryEntity.FILE_FORMAT] = list(set(file_formats))
            
        # API extraction
        api_endpoints = []
        for pattern in self.api_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            api_endpoints.extend(matches)
        if api_endpoints:
            entities[QueryEntity.API_ENDPOINT] = list(set(api_endpoints))
            
        return entities
        
    def _extract_with_spacy(self, query: str) -> Dict[QueryEntity, List[str]]:
        """Extract entities using spaCy NLP"""
        entities = {}
        
        try:
            doc = self.nlp(query)
            
            # Extract named entities
            for ent in doc.ents:
                if ent.label_ == 'GPE':  # Geographical location
                    if QueryEntity.LOCATION not in entities:
                        entities[QueryEntity.LOCATION] = []
                    entities[QueryEntity.LOCATION].append(ent.text)
                elif ent.label_ == 'ORG':  # Organization (could be satellite mission)
                    if QueryEntity.SATELLITE not in entities:
                        entities[QueryEntity.SATELLITE] = []
                    entities[QueryEntity.SATELLITE].append(ent.text)
                elif ent.label_ == 'PRODUCT':  # Product (could be data type)
                    if QueryEntity.DATA_TYPE not in entities:
                        entities[QueryEntity.DATA_TYPE] = []
                    entities[QueryEntity.DATA_TYPE].append(ent.text)
                    
            # Extract noun phrases
            noun_chunks = [chunk.text for chunk in doc.noun_chunks]
            if noun_chunks:
                # Look for specific patterns in noun chunks
                for chunk in noun_chunks:
                    chunk_lower = chunk.lower()
                    if any(word in chunk_lower for word in ['satellite', 'mission', 'data']):
                        if QueryEntity.SATELLITE not in entities:
                            entities[QueryEntity.SATELLITE] = []
                        entities[QueryEntity.SATELLITE].append(chunk)
                    elif any(word in chunk_lower for word in ['sensor', 'instrument']):
                        if QueryEntity.SENSOR not in entities:
                            entities[QueryEntity.SENSOR] = []
                        entities[QueryEntity.SENSOR].append(chunk)
                        
        except Exception as e:
            self.logger.error(f"Error in spaCy entity extraction: {e}")
            
        return entities
        
    def _classify_intent(self, query: str, entities: Dict[QueryEntity, List[str]]) -> Tuple[QueryIntent, float]:
        """
        Classify query intent
        
        Args:
            query: Preprocessed query string
            entities: Extracted entities
            
        Returns:
            Tuple of (intent, confidence)
        """
        # Define intent keywords
        intent_keywords = {
            QueryIntent.INFORMATION_RETRIEVAL: [
                'what', 'how', 'where', 'when', 'which', 'tell me', 'explain',
                'information', 'details', 'about', 'describe'
            ],
            QueryIntent.DATA_DOWNLOAD: [
                'download', 'get', 'obtain', 'access', 'retrieve', 'fetch',
                'data', 'file', 'product', 'imagery'
            ],
            QueryIntent.TECHNICAL_SUPPORT: [
                'help', 'support', 'problem', 'issue', 'error', 'trouble',
                'fix', 'resolve', 'work', 'function'
            ],
            QueryIntent.GEOSPATIAL_QUERY: [
                'location', 'area', 'region', 'coordinates', 'latitude', 'longitude',
                'spatial', 'geographic', 'map', 'boundary'
            ],
            QueryIntent.API_HELP: [
                'api', 'endpoint', 'service', 'call', 'request', 'response',
                'code', 'example', 'documentation', 'integration'
            ]
        }
        
        # Calculate scores for each intent
        scores = {}
        for intent, keywords in intent_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in query:
                    score += 1
            scores[intent] = score
            
        # Consider entities in intent classification
        if QueryEntity.LOCATION in entities:
            scores[QueryIntent.GEOSPATIAL_QUERY] += 2
        if QueryEntity.API_ENDPOINT in entities:
            scores[QueryIntent.API_HELP] += 2
        if QueryEntity.FILE_FORMAT in entities:
            scores[QueryIntent.DATA_DOWNLOAD] += 1
            
        # Find intent with highest score
        if not scores or max(scores.values()) == 0:
            return QueryIntent.GENERAL_QUESTION, 0.5
            
        best_intent = max(scores, key=scores.get)
        max_score = max(scores.values())
        total_possible = sum(len(keywords) for keywords in intent_keywords.values())
        
        confidence = min(max_score / total_possible, 1.0)
        
        return best_intent, confidence
        
    def _extract_keywords(self, query: str) -> List[str]:
        """
        Extract important keywords from query
        
        Args:
            query: Preprocessed query string
            
        Returns:
            List of extracted keywords
        """
        if not self.nlp:
            # Fallback: extract words longer than 3 characters
            words = query.split()
            return [word for word in words if len(word) > 3]
            
        try:
            doc = self.nlp(query)
            
            # Extract nouns, verbs, and adjectives
            keywords = []
            for token in doc:
                if (token.pos_ in ['NOUN', 'VERB', 'ADJ'] and 
                    not token.is_stop and 
                    len(token.text) > 2):
                    keywords.append(token.lemma_.lower())
                    
            # Add named entities
            for ent in doc.ents:
                keywords.append(ent.text.lower())
                
            return list(set(keywords))
            
        except Exception as e:
            self.logger.error(f"Error extracting keywords: {e}")
            # Fallback
            words = query.split()
            return [word for word in words if len(word) > 3]
            
    def get_query_suggestions(self, query: str, limit: int = 5) -> List[str]:
        """
        Get query suggestions based on input
        
        Args:
            query: User query
            limit: Maximum number of suggestions
            
        Returns:
            List of query suggestions
        """
        suggestions = []
        
        # Common MOSDAC-related queries
        common_queries = [
            "What satellite data is available for my region?",
            "How do I download satellite imagery?",
            "What is the spatial resolution of the data?",
            "How do I use the MOSDAC API?",
            "What sensors are available?",
            "How do I access historical data?",
            "What file formats are supported?",
            "How do I get technical support?"
        ]
        
        # Find relevant suggestions based on query content
        query_lower = query.lower()
        for suggestion in common_queries:
            if any(word in query_lower for word in suggestion.lower().split()):
                suggestions.append(suggestion)
                
        # Add general suggestions if not enough specific ones
        while len(suggestions) < limit and len(suggestions) < len(common_queries):
            for suggestion in common_queries:
                if suggestion not in suggestions:
                    suggestions.append(suggestion)
                    break
                    
        return suggestions[:limit]
        
    def enhance_query(self, query: str) -> str:
        """
        Enhance query with additional context
        
        Args:
            query: Original query
            
        Returns:
            Enhanced query
        """
        # Add MOSDAC context if not present
        if 'mosdac' not in query.lower():
            query = f"MOSDAC: {query}"
            
        # Add satellite context if not present
        if not any(word in query.lower() for word in ['satellite', 'data', 'imagery', 'remote sensing']):
            query = f"{query} satellite data"
            
        return query
