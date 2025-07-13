# SSO Authentication Application

A modern Single Sign-On (SSO) solution built with SvelteKit frontend and Python FastAPI backend, integrated with Azure Entra ID (Microsoft Identity Platform).

## 🏗️ Architecture

- **Frontend**: SvelteKit with TypeScript
- **Backend**: Python FastAPI with Azure MSAL
- **Identity Provider**: Azure Entra ID
- **Authentication Flow**: OAuth 2.0 Authorization Code Flow with PKCE
- **Deployment**: Azure Container Apps (Backend) + Azure Static Web Apps (Frontend)

## 🚀 Features

- ✅ Secure OAuth 2.0 with PKCE implementation
- ✅ JWT token management with automatic refresh
- ✅ Modern responsive UI with Svelte
- ✅ RESTful API with FastAPI
- ✅ Azure-ready infrastructure as code (Bicep)
- ✅ Comprehensive logging and monitoring
- ✅ Security best practices implemented

## 📋 Prerequisites

- **Development**:
  - Node.js 18+ and npm
  - Python 3.12+
  - Git

- **Azure Resources**:
  - Azure subscription
  - Azure Entra ID application registration
  - Azure CLI or Azure Developer CLI (azd)

## 🛠️ Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd auth-app
```

### 2. Azure Entra ID Configuration

1. Register a new application in Azure Entra ID:
   - Go to Azure Portal > Azure Entra ID > App registrations
   - Click "New registration"
   - Set redirect URI: `http://localhost:8000/auth/callback`
   - Note down: Application (client) ID, Directory (tenant) ID
   - Create a client secret and note it down

### 3. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup development environment
python dev_setup.py

# Update .env file with your Azure AD values:
# AZURE_CLIENT_ID=your-client-id
# AZURE_CLIENT_SECRET=your-client-secret  
# AZURE_TENANT_ID=your-tenant-id
```

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 5. Start Development Servers

**Backend (Terminal 1):**
```bash
cd backend
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

**Frontend (Terminal 2):**
```bash
cd frontend  
npm run dev
```

Access the application:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## 🌐 Deployment to Azure

### Using Azure Developer CLI (Recommended)

1. **Install Azure Developer CLI**:
   ```bash
   # Windows (PowerShell)
   winget install microsoft.azd
   
   # macOS
   brew tap azure/azd && brew install azd
   
   # Linux
   curl -fsSL https://aka.ms/install-azd.sh | bash
   ```

2. **Initialize and Deploy**:
   ```bash
   # Login to Azure
   azd auth login
   
   # Initialize the project
   azd init
   
   # Deploy to Azure
   azd up
   ```

3. **Configure Azure Resources**:
   - Update Azure Entra ID redirect URI to your deployed backend URL
   - Set production environment variables in Azure

### Manual Deployment

See the `infra/` directory for Bicep templates that can be deployed using Azure CLI.

## 📁 Project Structure

```
auth-app/
├── frontend/                 # SvelteKit frontend application
│   ├── src/
│   │   ├── lib/
│   │   │   ├── auth/        # Authentication logic
│   │   │   ├── components/  # Reusable Svelte components
│   │   │   └── utils/       # Utility functions
│   │   ├── routes/          # SvelteKit routes
│   │   └── app.html         # Main HTML template
│   ├── package.json
│   └── vite.config.js
├── backend/                  # Python FastAPI backend
│   ├── auth/                # Authentication modules
│   ├── models/              # Database models  
│   ├── app.py               # Main FastAPI application
│   ├── config.py            # Configuration management
│   ├── database.py          # Database setup
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile           # Container configuration
├── infra/                   # Azure infrastructure (Bicep)
│   ├── main.bicep           # Main infrastructure template
│   ├── core/                # Reusable infrastructure modules
│   └── app/                 # Application-specific resources
└── azure.yaml               # Azure Developer CLI configuration
```

## 🔒 Security Features

- **PKCE (Proof Key for Code Exchange)**: Protects against authorization code interception
- **JWT Token Security**: Short-lived access tokens with secure refresh mechanism
- **HttpOnly Cookies**: Refresh tokens stored in secure, HttpOnly cookies
- **CORS Protection**: Properly configured cross-origin resource sharing
- **Input Validation**: Comprehensive validation on all API endpoints
- **Security Headers**: Security headers implemented via middleware
- **Managed Identity**: Azure resources use managed identity for secure access

## 🧪 Testing

**Backend Tests:**
```bash
cd backend
pytest
```

**Frontend Tests:**
```bash
cd frontend
npm run test
```

## 📊 Monitoring and Logging

- **Application Insights**: Comprehensive application monitoring
- **Structured Logging**: JSON-formatted logs with correlation IDs
- **Health Checks**: Built-in health check endpoints
- **Performance Monitoring**: Request/response time tracking

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure backend ALLOWED_ORIGINS includes your frontend URL
2. **Token Refresh Issues**: Check that cookies are enabled and HTTPS is used in production
3. **Azure AD Errors**: Verify redirect URI matches exactly in Azure AD configuration
4. **Database Issues**: Ensure database URL is correct and accessible

### Getting Help

- Check the [Issues](../../issues) for known problems
- Review logs in Azure Application Insights
- Validate Azure AD configuration in Azure Portal

## 🔗 Useful Links

- [Azure Entra ID Documentation](https://docs.microsoft.com/en-us/azure/active-directory/)
- [SvelteKit Documentation](https://kit.svelte.dev/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Azure Developer CLI](https://docs.microsoft.com/en-us/azure/developer/azure-developer-cli/)
