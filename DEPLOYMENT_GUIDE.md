# Deployment Guide: Render + Vercel + Supabase

This guide details how to deploy your Stock Portfolio application.

## Prerequisites
- GitHub account (push your code to a repository).
- Accounts on [Render](https://render.com), [Vercel](https://vercel.com), and [Supabase](https://supabase.com).

## Part 1: Database (Supabase)

1.  **Create Project:** Log in to Supabase and create a new project.
2.  **Get Credentials:** Go to **Project Settings > API**. Copy the `Project URL` and `anon public` Key. You will need these later.
3.  **Create Table:**
    - Go to the **Table Editor**.
    - Create a new table named `holdings`.
    - Enable RLS (Row Level Security) if you want security, but for a personal project, you can leave it off initially or configure policies later.
    - Add the following columns:
        - `symbol` (text, Primary Key)
        - `shares` (int8)
        - `cost_basis` (float8)
        - `updated_at` (timestamptz)
4.  **Migrate Data (Optional):**
    - If you have data in `portfolio.json`, run the migration script locally:
      1. Create a `.env` file with `SUPABASE_URL` and `SUPABASE_KEY`.
      2. Run `python migrate_to_supabase.py`.

## Part 2: Backend (Render)

1.  **New Web Service:** Log in to Render and create a **New Web Service**.
2.  **Connect Repo:** Connect your GitHub repository.
3.  **Settings:**
    - **Name:** `stock-portfolio-backend` (or similar)
    - **Runtime:** `Docker` (Render should detect the Dockerfile)
    - **Region:** Choose one close to you (e.g., Singapore for better connectivity from China, or US West).
4.  **Environment Variables:**
    Add the following environment variables:
    - `SUPABASE_URL`: (Paste from Supabase)
    - `SUPABASE_KEY`: (Paste from Supabase)
    - `GEMINI_API_KEY`: (Your Gemini API Key)
    - `PORT`: `10000` (Optional, Render sets this automatically, but good to be explicit)
5.  **Deploy:** Click **Create Web Service**. Wait for the build to finish.
    - *Note: The build might take a few minutes as it compiles TA-Lib.*
6.  **Get URL:** Once deployed, copy the service URL (e.g., `https://stock-portfolio-backend.onrender.com`).

## Part 3: Frontend (Vercel)

1.  **New Project:** Log in to Vercel and click **Add New > Project**.
2.  **Connect Repo:** Import the same GitHub repository.
3.  **Configure Project:**
    - **Framework Preset:** Vercel should auto-detect `Vite`.
    - **Root Directory:** Click `Edit` and select `client`. **(Important!)**
4.  **Environment Variables:**
    - Add `VITE_API_URL` with the value of your Render backend URL (e.g., `https://stock-portfolio-backend.onrender.com`).
    - *Note: Do not add a trailing slash `/`.*
5.  **Deploy:** Click **Deploy**.

## Part 4: Final Verification

1.  Open your Vercel app URL.
2.  The dashboard should load.
3.  It might take a moment for the Render backend to wake up (free tier spins down after inactivity).
4.  Try adding a stock. It should save to Supabase.
