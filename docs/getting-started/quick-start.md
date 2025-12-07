# 🚀 Quick Start Guide

Get up and running with Agent47 in minutes! This guide will help you set up the platform and start using our AI agents.

## 📋 Prerequisites

Before you begin, ensure you have:

- **Docker & Docker Compose** installed
- **Git** for cloning the repository
- **Basic terminal/command line knowledge**
- **Internet connection** for downloading dependencies

## ⚡ 5-Minute Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-org/agent47.git
cd agent47
```

### Step 2: Configure Environment

```bash
# Copy environment template
cp env.example .env

# Edit configuration (optional for quick start)
nano .env
```

### Step 3: Start the Platform

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps
```

### Step 4: Access the Platform

Open your browser and navigate to:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Step 5: Create Your First Account

1. Go to http://localhost:3000
2. Click "Sign Up"
3. Enter your email and password
4. Choose your subscription plan
5. Start using the AI agents!

## 🎯 Your First AI Agent

### Using Aria (Content Creation)

1. **Navigate to Aria**: Click on the Aria agent card
2. **Start a Chat**: Click the chat button
3. **Ask for Content**: Try "Create a blog post about AI trends"
4. **Review Results**: Aria will generate content for you

### Using Clara (Customer Support)

1. **Go to Clara**: Click on the Clara agent card
2. **Set Up Knowledge Base**: Upload your FAQ documents
3. **Test Support**: Ask a question about your business
4. **Monitor Performance**: Check response quality

## 🔧 Basic Configuration

### Environment Variables

Key settings in your `.env` file:

```bash
# Database (default values work for local development)
DB_POSTGRES_HOST=localhost
DB_POSTGRES_PORT=5432
DB_POSTGRES_USER=agent47
DB_POSTGRES_PASSWORD=agent47_password
DB_POSTGRES_DB=agent47_db

# AI Services (add your API keys)
CHUTES_API_KEY=your_chutes_api_key_here
GROK_API_URL=http://localhost:8001

# Security (change in production)
SECURITY_SECRET_KEY=your-secret-key-change-in-production
```

### Subscription Plans

Choose the right plan for your needs:

| Plan | Agents | Price | Best For |
|------|--------|-------|----------|
| **Free** | 1 agent | $0/month | Testing & exploration |
| **Starter** | 4 agents | $29/month | Small businesses |
| **Pro** | All 7 agents | $99/month | Growing businesses |

## 🎮 Try These Examples

### Content Creation with Aria

```
User: "Create a social media post about our new product launch"
Aria: [Generates engaging social media content with hashtags and call-to-action]
```

### Customer Support with Clara

```
User: "What's your return policy?"
Clara: [Provides detailed return policy information from knowledge base]
```

### Sales with Eric

```
User: "Generate a sales email for our premium plan"
Eric: [Creates personalized sales email with pricing and benefits]
```

### Marketing with Jackie

```
User: "Create a marketing campaign for Black Friday"
Jackie: [Develops comprehensive campaign strategy with content calendar]
```

### Research with Joe

```
User: "Analyze our competitors' pricing strategies"
Joe: [Researches and analyzes competitor pricing data]
```

### Business with Purity

```
User: "Help me create a business plan for my startup"
Purity: [Generates comprehensive business plan with financial projections]
```

### Writing with Shakes

```
User: "Write a product description for our new app"
Shakes: [Creates compelling product description with SEO optimization]
```

## 🚨 Troubleshooting

### Common Issues

#### Services Not Starting

```bash
# Check Docker status
docker --version
docker-compose --version

# Check service logs
docker-compose logs [service-name]

# Restart services
docker-compose restart
```

#### Database Connection Issues

```bash
# Check PostgreSQL
docker-compose exec postgres pg_isready

# Check Redis
docker-compose exec redis redis-cli ping

# Check Kafka
docker-compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list
```

#### Frontend Not Loading

```bash
# Check frontend logs
docker-compose logs frontend

# Restart frontend
docker-compose restart frontend

# Check if port 3000 is available
lsof -i :3000
```

### Getting Help

- **Documentation**: Check the full documentation
- **GitHub Issues**: Report bugs and request features
- **Discord**: Join our community for support
- **Email**: Contact support@agent47.app

## 🎉 Next Steps

Now that you have Agent47 running:

1. **Explore the Agents**: Try different AI agents and their capabilities
2. **Create Workflows**: Set up automated processes between agents
3. **Customize Settings**: Configure agents for your specific needs
4. **Scale Up**: Upgrade your subscription as you grow
5. **Join Community**: Connect with other users and share experiences

## 📚 Additional Resources

- [Complete Installation Guide](installation.md)
- [Configuration Guide](configuration.md)
- [Agent Documentation](../../agents/overview.md)
- [API Reference](../../development/api-reference.md)
- [Troubleshooting Guide](../../operations/troubleshooting.md)

## 🆘 Need Help?

- **Quick Questions**: Check our [FAQ](faq.md)
- **Technical Issues**: [GitHub Issues](https://github.com/your-org/agent47/issues)
- **Community Support**: [Discord](https://discord.gg/agent47)
- **Enterprise Support**: [Contact Sales](mailto:sales@agent47.app)

---

**Welcome to Agent47! 🎉**

*Start automating your business with AI agents today.*
