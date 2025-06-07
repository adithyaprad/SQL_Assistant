# 🤖 SQL Assistant with Google OAuth Integration

A powerful application that combines Google OAuth authentication with an intelligent SQL assistant powered by Agent SDK. Users authenticate with Google accounts to access an agent interface that converts natural language to optimized SQL queries for MySQL databases.

## 📊 Project Demo
https://github.com/user-attachments/assets/88d80b76-13bf-4ae4-82d0-c10c215fa830

## 🔄 Flow of Events
![Image](https://github.com/user-attachments/assets/b3dc87bd-a279-4fa7-b536-13c1a9eee8de)

## 🌟 Features

- **Secure Authentication**: Google OAuth integration for user login
- **Multi-agent SQL Pipeline**: Converts natural language to SQL through:
  - Requirements Analysis
  - SQL Generation
  - Code Review
  - Query Optimization
  - Execution
- **Interactive UI**: Clean interface for queries and results
- **Query History**: Track previous queries and results
- **Database Management**: Create and manage databases through natural language

## 📋 Prerequisites

- Python 3.7+
- MySQL server
- Google Cloud Platform account with OAuth credentials
- ADK (Agent Development Kit) CLI tool

## 🚀 Setup Instructions

1. **Clone the Repository**

```bash
git clone https://github.com/adithyaprad/SQL_assistant.git
cd SQL_assistant
```

2. **Create a Virtual Environment**

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python -m venv venv
source venv/bin/activate
```

3. **Install Dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure Google OAuth Credentials**

- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Create/select a project
- Navigate to "APIs & Services" > "Credentials"
- Click "Create Credentials" > "OAuth client ID"
- Set application type to "Web application"
- Add redirect URIs (e.g., `http://localhost:5000/callback`)
- Copy Client ID and Client Secret

5. **Set Up Environment Variables**

```bash
cp .env.sample .env
```

Edit `.env` file:

```
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
SECRET_KEY=your-secret-key
DB_HOST=localhost
DB_USER=your_db_username
DB_PASSWORD=your_db_password
DB_NAME=your_db_name
```

6. **Run the Application**

```bash
python app.py
```

Access at `http://localhost:5000`

## 💻 Usage Guide

1. **Authentication**: Navigate to `http://localhost:5000` and click "Login with Google"

2. **Starting the Agent**: After login, click "Start ADK Web" to initialize the agent

3. **Example Queries**:
   - "Create a database named 'inventory'"
   - "Create a table for products with columns for name, price, and quantity"
   - "Find all products with price greater than $50"
   - "Show me the average price of products by category"
   - "List the top 5 most expensive products"

4. **Results & History**: View query results and access previous queries from the history panel

## 🏗️ Architecture

### Components

- **Flask**: Web framework
- **Authlib**: OAuth client for Google authentication
- **Google ADK**: Agent Development Kit
- **MySQL**: Database for SQL queries
- **Sequential Agent Pattern**: Multiple specialized agents in a pipeline

### Agent Pipeline

1. **SQL Requirements Analyzer**: Extracts key requirements from natural language
2. **SQL Generator**: Creates initial SQL query
3. **SQL Reviewer**: Reviews and suggests improvements
4. **SQL Optimizer**: Optimizes the query
5. **SQL Execution**: Runs the query and returns formatted results

## 🔒 Security Notes

- Environment variables for all sensitive information
- OAuth for secure authentication
- Secured session cookies with HTTP-only flag
- No hardcoded database credentials

## 🛠️ Troubleshooting

- **Authentication Issues**: Verify Google OAuth credentials and redirect URI
- **Database Connection Errors**: Check MySQL server status and credentials
- **Agent Errors**: Ensure ADK Web service is running properly

## 👥 Contributing

Contributions welcome! Submit a Pull Request or open an Issue on GitHub.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details. 
