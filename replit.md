# ABL Analytics Dashboard

## Overview

The ABL Analytics Dashboard is a comprehensive Streamlit-based web application for analyzing fantasy baseball league data. It provides interactive visualizations and analytics for the American Baseball League (ABL), integrating data from the Fantrax fantasy platform to deliver insights on rosters, standings, player values, prospects, and trade analysis.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit web application with custom CSS styling
- **Visualization**: Plotly for interactive charts and graphs
- **UI Components**: Modular component system with dedicated files for each feature
- **Styling**: Custom CSS with animated backgrounds, particle effects, and responsive design
- **Page Configuration**: Wide layout with collapsible sidebar

### Backend Architecture
- **API Integration**: Custom API client for Fantrax platform
- **Data Processing**: Dedicated data processor for cleaning and transforming API responses
- **Error Handling**: Retry mechanisms with exponential backoff for API requests
- **Caching**: Streamlit's built-in caching for performance optimization

### Component Structure
The application follows a modular component architecture:
- `components/`: Individual feature modules (rosters, standings, prospects, etc.)
- `api_client.py`: Handles all external API communications
- `data_processor.py`: Processes and normalizes raw data
- `utils.py`: Utility functions and data management
- `app.py`: Main application entry point

## Key Components

### 1. API Client (`api_client.py`)
- **Purpose**: Interface with Fantrax API for league data
- **Features**: 
  - Retry strategy with exponential backoff
  - Error handling for API failures
  - Mock data fallback for development
  - Session management with connection pooling

### 2. Data Processor (`data_processor.py`)
- **Purpose**: Clean and normalize data from various sources
- **Features**:
  - Player name normalization for cross-dataset matching
  - Roster data processing and team assignment
  - Unicode handling for international player names

### 3. Component Modules
- **League Info**: Basic league information and welcome interface
- **Rosters**: Team roster management and player statistics
- **Standings**: League standings with win/loss records
- **Power Rankings**: Team power rankings with historical tracking
- **MVP Race**: Player value assessment using comprehensive scoring
- **Prospects**: Prospect analysis and rankings
- **DDI (Dynasty Dominance Index)**: Multi-factor team strength analysis
- **Trade Analysis**: Dump deadline trade evaluation
- **Transactions**: Transaction history and filtering

### 4. Analytics Engine
- **MVP Scoring**: Multi-factor player valuation algorithm
- **DDI Calculation**: Dynasty strength assessment combining current performance, prospects, and history
- **Trade Analysis**: Value-based trade assessment with win/loss determination

## Data Flow

### 1. Data Acquisition
- API calls to Fantrax platform for real-time league data
- CSV file imports for supplementary data (MVP lists, prospect rankings)
- Historical data loading from local storage

### 2. Data Processing
- Name normalization for player matching across datasets
- Statistical calculations for fantasy point scoring
- Team assignment and roster organization

### 3. Analytics Computation
- MVP score calculation using weighted factors
- DDI score computation with historical performance
- Trade value assessment with comprehensive player valuation

### 4. Visualization
- Interactive charts using Plotly
- Responsive tables with Streamlit dataframes
- Custom HTML components for enhanced UI

## External Dependencies

### Core Libraries
- **Streamlit**: Web application framework
- **Pandas**: Data manipulation and analysis
- **Plotly**: Interactive visualization
- **Requests**: HTTP client for API calls
- **NumPy**: Numerical computations

### API Integration
- **Fantrax API**: Primary data source for league information
- **MLB API**: Player images and supplementary data

### Data Sources
- **CSV Files**: MVP rankings, prospect data, historical records
- **API Endpoints**: Real-time league data, rosters, standings

## Deployment Strategy

### Development Environment
- **Container**: Python 3.11 development container
- **IDE**: VS Code with Python extensions
- **Package Management**: pip with requirements.txt

### Application Configuration
- **Port**: 8501 (Streamlit default)
- **CORS**: Disabled for development
- **XSRF Protection**: Disabled for development

### File Structure
- **Static Assets**: `attached_assets/` directory for CSV files and images
- **Components**: Modular component files in `components/` directory
- **Configuration**: DevContainer setup for consistent development environment

### Performance Considerations
- **Caching**: Streamlit cache decorators for API calls
- **Lazy Loading**: Components loaded on demand
- **Error Recovery**: Graceful degradation with mock data fallback

### Security Features
- **Input Validation**: Data type checking and sanitization
- **Error Handling**: Comprehensive exception management
- **Rate Limiting**: Built into API client retry strategy

The application is designed to be maintainable, scalable, and user-friendly, with a focus on providing actionable insights for fantasy baseball league management.