# RAPID-100 Architecture Diagram

```mermaid
graph TB
    subgraph "Frontend Layer"
        A[Dispatcher Dashboard - React/Tailwind]
        B[WebSocket Client]
    end

    subgraph "Backend Layer"
        C[FastAPI Server]
        D[WebSocket Endpoint]
        E[REST API Endpoints]
    end

    subgraph "AI Services"
        F[Transcription Service - Whisper]
        G[Classification Service - DistilBERT/NLP]
        H[Severity Service - Rule-based/ML]
        I[Location Service - NER/spaCy]
        J[Explanation Service - SHAP/Attention]
    end

    subgraph "Utils Layer"
        K[Audio Processing]
        L[Logging Service]
    end

    subgraph "Data Layer"
        M[Call Logs - JSON]
        N[Sample Data - CSV]
    end

    A --> B
    B --> D
    C --> D
    C --> E
    D --> F
    E --> G
    E --> H
    E --> I
    E --> J
    F --> K
    G --> K
    H --> K
    I --> K
    J --> L
    F --> G
    G --> H
    H --> I
    I --> J
    L --> M
    K --> N
```

## System Components

### Frontend (React + Tailwind)
- Dispatcher dashboard with real-time updates
- Live call panel showing transcription
- Summary panel with structured data
- Routing panel with department suggestions
- Explainability panel with highlighted phrases
- Timeline view showing AI decision process

### Backend (Python + FastAPI)
- RESTful API endpoints for classification and simulation
- WebSocket endpoint for real-time transcription streaming
- Modular service architecture
- Async processing for performance

### AI Services
- **Transcription Service**: Converts speech to text using Whisper
- **Classification Service**: Determines emergency type using NLP
- **Severity Service**: Assigns priority level based on keywords/rules
- **Location Service**: Extracts location information using NER
- **Explanation Service**: Provides reasoning for AI decisions

### Data & Logging
- Structured JSON logging for auditability
- Sample dataset for testing and training
- Performance metrics tracking