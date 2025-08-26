# MOSDAC AI Help Bot

An intelligent virtual assistant leveraging NLP/ML for query understanding and precise information retrieval from the MOSDAC portal (www.mosdac.gov.in).

## 🎯 Objective

Develop an intelligent virtual assistant that:
- Leverages NLP/ML for query understanding and precise information retrieval
- Extracts and models structured/unstructured content into a dynamic knowledge graph
- Supports geospatial data intelligence for spatially-aware question answering
- Ensures contextual, relationship-based information discovery
- Maintains modularity for deployment across other web portals with similar architectures

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Portal   │    │  Content       │    │  Knowledge     │
│   Scraping     │───▶│  Processing    │───▶│  Graph         │
│   Module       │    │  Pipeline      │    │  Construction  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   NLP/ML       │    │  Query          │    │  Response      │
│   Pipeline     │◀───│  Understanding  │◀───│  Generation    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Geospatial    │
                       │  Intelligence  │
                       └─────────────────┘
```

## 🚀 Features

### Core Capabilities
- **Intelligent Content Scraping**: Automated extraction from MOSDAC portal
- **Knowledge Graph Construction**: Dynamic graph-based information organization
- **Advanced NLP Processing**: Context-aware query understanding
- **Geospatial Intelligence**: Spatial query handling and visualization
- **Modular Architecture**: Easy deployment to other web portals

### Technical Features
- **Multi-format Support**: HTML, PDF, API data extraction
- **Real-time Updates**: Dynamic knowledge graph updates
- **Contextual Responses**: Relationship-based information retrieval
- **Scalable Design**: Microservices architecture
- **API-First Approach**: RESTful and GraphQL endpoints

## 📁 Project Structure

```
mosdac/
├── src/
│   ├── scrapers/          # Web scraping modules
│   ├── processors/        # Content processing pipeline
│   ├── knowledge_graph/   # Knowledge graph construction
│   ├── nlp/              # NLP/ML processing
│   ├── geospatial/       # Geospatial intelligence
│   ├── api/              # FastAPI backend
│   ├── web/              # Streamlit frontend
│   └── utils/            # Utility functions
├── data/                 # Data storage
├── models/               # Trained ML models
├── config/               # Configuration files
├── tests/                # Test suite
├── docs/                 # Documentation
└── deployment/           # Deployment scripts
```

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd mosdac
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download required models**
   ```bash
   python -m spacy download en_core_web_sm
   python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
   ```

5. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## 🚀 Quick Start

### Start the AI Help Bot

1. **Launch the backend API**
   ```bash
   cd src/api
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Launch the web interface**
   ```bash
   cd src/web
   streamlit run app.py
   ```

3. **Access the system**
   - API Documentation: http://localhost:8000/docs
   - Web Interface: http://localhost:8501

### Basic Usage

```python
from src.nlp.query_processor import QueryProcessor
from src.knowledge_graph.graph_manager import GraphManager

# Initialize components
processor = QueryProcessor()
graph = GraphManager()

# Process a query
query = "What satellite data is available for Mumbai region?"
response = processor.process_query(query, graph)
print(response)
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# Database Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# MOSDAC Portal Configuration
MOSDAC_BASE_URL=https://www.mosdac.gov.in
MOSDAC_API_KEY=your_api_key_if_available

# Scraping Configuration
SCRAPING_DELAY=1
MAX_CONCURRENT_REQUESTS=5

# Model Configuration
MODEL_CACHE_DIR=./models
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

## 📊 Data Sources

The system extracts information from:

- **Static Content**: HTML pages, documentation, FAQs
- **Dynamic Content**: API responses, real-time data
- **Structured Data**: CSV, JSON, XML files
- **Unstructured Data**: Text documents, images (OCR)
- **Geospatial Data**: Shapefiles, GeoJSON, satellite imagery metadata

## 🧠 AI/ML Components

### Natural Language Processing
- **Query Understanding**: Intent classification, entity extraction
- **Semantic Search**: Vector-based similarity matching
- **Context Awareness**: Conversation history and relationship tracking

### Machine Learning Models
- **Embedding Models**: Sentence transformers for semantic understanding
- **Classification Models**: Intent and entity classification
- **Recommendation Systems**: Content and query suggestions

### Knowledge Graph
- **Graph Construction**: Automated relationship extraction
- **Graph Embeddings**: Node and edge representations
- **Graph Queries**: Cypher and SPARQL query support

## 🌍 Geospatial Intelligence

- **Spatial Queries**: Location-based question answering
- **Map Visualization**: Interactive maps with data overlays
- **Coordinate Systems**: Support for multiple CRS
- **Spatial Analysis**: Buffer, intersection, and proximity queries

## 🔌 API Endpoints

### Core Endpoints
- `POST /query` - Process user queries
- `GET /knowledge/{entity}` - Retrieve entity information
- `POST /feedback` - Collect user feedback
- `GET /status` - System health and status

### Graph Endpoints
- `GET /graph/entities` - List all entities
- `GET /graph/relationships` - List entity relationships
- `POST /graph/query` - Execute graph queries

### Geospatial Endpoints
- `GET /spatial/bounds` - Get spatial boundaries
- `POST /spatial/query` - Execute spatial queries
- `GET /spatial/visualize` - Generate map visualizations

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run specific test modules
pytest tests/test_nlp.py
pytest tests/test_knowledge_graph.py

# Run with coverage
pytest --cov=src tests/
```

## 📈 Performance Metrics

- **Query Response Time**: < 2 seconds for 95% of queries
- **Accuracy**: > 90% for intent classification
- **Scalability**: Support for 1000+ concurrent users
- **Uptime**: 99.9% availability

## 🔒 Security

- **Input Validation**: Comprehensive query sanitization
- **Rate Limiting**: API usage throttling
- **Authentication**: JWT-based user authentication
- **Data Privacy**: GDPR-compliant data handling

## 🚀 Deployment

### Docker Deployment

```bash
# Build the image
docker build -t mosdac-ai-bot .

# Run the container
docker run -p 8000:8000 -p 8501:8501 mosdac-ai-bot
```

### Kubernetes Deployment

```bash
kubectl apply -f deployment/k8s/
```

### Cloud Deployment

- **AWS**: ECS/EKS with RDS and ElastiCache
- **Azure**: AKS with Azure Database and Redis
- **GCP**: GKE with Cloud SQL and Memorystore

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation

## 🔮 Roadmap

### Phase 1 (Current)
- [x] Basic architecture design
- [x] Core scraping functionality
- [x] Knowledge graph construction
- [x] Basic NLP pipeline

### Phase 2 (Next)
- [ ] Advanced geospatial features
- [ ] Multi-language support
- [ ] Advanced ML models
- [ ] Performance optimization

### Phase 3 (Future)
- [ ] Real-time data integration
- [ ] Advanced analytics dashboard
- [ ] Mobile application
- [ ] Enterprise features
