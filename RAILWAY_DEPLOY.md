# Railway Deployment Guide

## Prerequisites
1. A Railway account (sign up at https://railway.app)
2. Your code pushed to GitHub (or GitLab/Bitbucket)

## Deployment Steps

### 1. Prepare Your Repository
- Make sure all files are committed to git
- Ensure `.gitignore` is set up correctly
- Your JSON data file (`courses_en.json`) should be in the repository root

### 2. Deploy to Railway

**Option A: Deploy from GitHub**
1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Connect your GitHub account and select your repository
5. Railway will automatically detect the project and deploy

**Option B: Deploy using Railway CLI**
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init

# Deploy
railway up
```

### 3. Set Environment Variables
In Railway dashboard, go to your project → Variables and add:
- `GROQ_API_KEY`: Your Groq API key (required for LLM)
- `PORT`: Railway sets this automatically, but you can override if needed

### 4. Build Configuration
Railway will automatically:
- Detect Python project
- Install dependencies from `requirements.txt`
- Use `Procfile` to start the application
- Use `nixpacks.toml` for build configuration (if needed)

### 5. Access Your App
- Railway will provide a public URL after deployment
- Your app will be available at: `https://your-app-name.railway.app`

## Files for Railway Deployment

- **Procfile**: Defines how to run your app
- **requirements.txt**: Lists Python dependencies
- **nixpacks.toml**: Build configuration (optional)
- **runtime.txt**: Python version specification (optional)
- **railway.json**: Railway-specific configuration (optional)

## Important Notes

1. **JSON File**: Make sure `courses_en.json` is in your repository root
2. **Environment Variables**: Set `GROQ_API_KEY` in Railway dashboard
3. **Port**: The app uses the `PORT` environment variable (Railway sets this automatically)
4. **Database**: ChromaDB will be created in the `chroma_db` directory (persistent storage on Railway)

## Troubleshooting

- Check Railway logs if deployment fails
- Ensure all environment variables are set
- Verify JSON file path is correct
- Check that all dependencies are in `requirements.txt`

