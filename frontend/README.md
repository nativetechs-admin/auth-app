# NECTARWORKS - Enterprise SSO Authentication Platform

A modern, enterprise-grade Single Sign-On (SSO) authentication platform built with SvelteKit frontend and Python FastAPI backend, integrated with Microsoft Azure Entra ID and Dataverse for comprehensive user management and project tracking.

## 🏗️ Architecture

**Frontend**: SvelteKit with TypeScript  
**Backend**: Python FastAPI with Azure MSAL  
**Identity Provider**: Azure Entra ID (Microsoft Identity Platform)  
**Data Platform**: Microsoft Dataverse  
**Authentication Flow**: OAuth 2.0 Authorization Code Flow with PKCE  
**Token Management**: Cookieless authentication using localStorage and Authorization headers

## ✨ Features

### 🔐 Authentication & Security
- **Microsoft Entra ID Integration**: Enterprise-grade SSO with Azure AD
- **PKCE Support**: Proof Key for Code Exchange for enhanced security
- **Cookieless Authentication**: Modern localStorage-based token management
- **Automatic Token Refresh**: Seamless session management with refresh tokens
- **Session Tracking**: Comprehensive audit logging in Microsoft Dataverse

### 👤 User Management
- **Azure AD User Sync**: Automatic user profile synchronization
- **Business Unit Integration**: Projects filtered by user's organizational unit
- **Session Auditing**: Detailed login tracking with IP, user agent, and timestamps

### 📋 Project Management
- **Dataverse Integration**: Direct connection to Microsoft Dataverse projects
- **Business Unit Filtering**: Users only see projects from their organizational unit
- **Project Details**: Comprehensive project information including status, timelines, and metadata
- **Responsive Design**: Optimized for desktop and mobile devices

### 🔧 Developer Experience
- **TypeScript Support**: Full type safety across frontend and backend
- **Modern UI Components**: Clean, accessible component library
- **API Documentation**: Comprehensive FastAPI auto-generated docs
- **Environment Configuration**: Flexible configuration for different deployment environments

## 🚀 Quick Start

### Prerequisites
- **Node.js** 18+ and npm
- **Python** 3.11+
- **Azure AD Application** with appropriate permissions
- **Microsoft Dataverse** environment access

### Development Setup

#### Frontend (Port: 5173)
```bash
cd frontend
npm install
npm run dev
```

#### Backend (Port: 8000)
```bash
cd backend
pip install -r requirements.txt
uvicorn app:app --reload
```

### Environment Configuration

Both frontend and backend require environment configuration files. Create `.env` files based on the provided examples with your Azure AD and Dataverse settings.

## 📁 Project Structure

```
auth-app/
├── frontend/               # SvelteKit frontend application
│   ├── src/
│   │   ├── lib/           # Shared components and utilities
│   │   │   ├── auth/      # Authentication services and stores
│   │   │   ├── components/ # Reusable UI components
│   │   │   └── utils/     # API client and helper functions
│   │   └── routes/        # SvelteKit file-based routing
│   │       ├── dashboard/ # Main dashboard page
│   │       ├── projects/  # Project management page
│   │       ├── login/     # Authentication entry point
│   │       └── callback/  # OAuth callback handler
│   └── static/            # Static assets
│
└── backend/               # FastAPI backend application
    ├── auth/              # Authentication modules
    │   ├── routes.py      # API endpoints
    │   ├── middleware.py  # JWT validation and user extraction
    │   └── models.py      # Data models
    ├── dataverse_service.py # Microsoft Dataverse integration
    ├── config.py          # Configuration management
    └── app.py             # FastAPI application entry point
```

## 🔌 API Endpoints

### Authentication
- `POST /auth/login` - Initiate OAuth flow
- `POST /auth/complete-auth` - Complete authentication and exchange tokens
- `GET /auth/user` - Get current user information
- `POST /auth/refresh` - Refresh access tokens
- `POST /auth/logout` - End user session

### Projects
- `GET /auth/projects` - Get user's business unit projects from Dataverse

### Health & Monitoring
- `GET /health` - Application health check
- `GET /docs` - Interactive API documentation

## 🛡️ Security Features

### Token Management
- **Short-lived Access Tokens**: 30-minute expiration for security
- **Refresh Token Rotation**: 7-day expiration with automatic renewal
- **Secure Storage**: localStorage with automatic cleanup on logout

### API Security
- **JWT Validation**: All protected endpoints validate access tokens
- **CORS Configuration**: Properly configured cross-origin requests
- **Input Validation**: Comprehensive request validation with Pydantic models

### Audit & Compliance
- **Session Logging**: All authentication events logged to Dataverse
- **User Activity Tracking**: IP addresses, user agents, and timestamps recorded
- **Integration Audit**: Dataverse relationships maintain data integrity

## 🌐 Deployment

### Production Architecture
- **Frontend**: Azure Static Web Apps for global CDN distribution
- **Backend**: Azure Container Apps for serverless container hosting
- **Monitoring**: Azure Application Insights for comprehensive observability

### Environment Support
- **Development**: Local development with hot reload
- **Staging**: Preview environments for testing
- **Production**: Scalable Azure-native deployment

## 🔧 Configuration

### Azure AD Requirements
- Application registration with appropriate redirect URIs
- API permissions for Microsoft Graph and Dataverse
- Client secret for backend authentication

### Dataverse Setup
- Custom entities for user sessions and project tracking
- Proper security roles and business unit configuration
- API access permissions for the service account

## 📊 Monitoring & Logging

### Application Logging
- Structured JSON logging with correlation IDs
- Comprehensive error tracking and performance metrics
- Debug modes for development troubleshooting

### Business Intelligence
- User authentication patterns and session analytics
- Project access tracking and usage statistics
- Integration health monitoring

## 🤝 Contributing

This is an enterprise authentication platform designed for organizational use. The codebase follows modern development practices with TypeScript, comprehensive error handling, and security-first design principles.

## 📄 License

Proprietary software for enterprise use.

---

**NECTARWORKS** - Streamlining enterprise authentication and project management through modern web technologies and Microsoft ecosystem integration.