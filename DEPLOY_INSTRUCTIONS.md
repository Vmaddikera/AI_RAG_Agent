# Railway Deployment Instructions

## Fix Git Push Error

If you get "error: src refspec main does not match any", follow these steps:

### Step 1: Initialize Git (if not already done)
```bash
git init
```

### Step 2: Add all files
```bash
git add .
```

### Step 3: Create initial commit
```bash
git commit -m "Initial commit: RAG Agent with Course Assistant"
```

### Step 4: Set up remote (if not already done)
```bash
git remote add origin https://github.com/Vmaddikera/AI_RAG_Agent.git
```

### Step 5: Push to GitHub
```bash
# If your default branch is main
git branch -M main
git push -u origin main

# OR if your default branch is master
git branch -M master
git push -u origin master
```

## Deploy to Railway

1. Go to https://railway.app
2. Sign up/Login
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Connect your GitHub account
6. Select the repository: `Vmaddikera/AI_RAG_Agent`
7. Railway will automatically detect and deploy

## Environment Variables

In Railway dashboard, add:
- `GROQ_API_KEY`: Your Groq API key

## Important Notes

- Make sure `courses_en.json` is in your repository root
- The app will be available at a Railway-provided URL
- ChromaDB will persist in Railway's filesystem

