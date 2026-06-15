# MindSense — Setup Guide (Supabase + Streamlit)

Ye guide aapko **step by step** batayegi ke free Supabase database + login/signup kaise setup karna hai, aur Streamlit pa kaise deploy karna hai.

---

## STEP 1: Supabase Account Banayein (FREE)

1. Jayein: https://supabase.com
2. **"Start your project"** pa click karein → GitHub se sign up karein (free)
3. **"New Project"** banayein:
   - Name: `mindsense` (ya kuch bhi)
   - Database Password: ek strong password set karein aur **save karke rakhein**
   - Region: jo bhi closest ho (e.g. Singapore)
   - Plan: **Free**
4. Project create hone mein 1-2 minute lagega.

---

## STEP 2: API Keys Copy Karein

1. Left sidebar mein **Settings** (gear icon) → **API** pa jayein
2. Wahan se ye 2 cheezein copy karein:
   - **Project URL** (e.g. `https://xxxxx.supabase.co`)
   - **anon public key** (lambi sa string)

Ye dono aapko `.streamlit/secrets.toml` mein dalni hongi (Step 5 mein).

---

## STEP 3: Database Table Banayein (Chat History ke liye)

1. Left sidebar mein **SQL Editor** pa jayein
2. **New Query** pa click karein aur ye SQL paste karein:

```sql
-- Chat messages table
create table public.chat_messages (
  id bigint generated always as identity primary key,
  user_id uuid references auth.users(id) on delete cascade not null,
  role text not null,           -- 'user' or 'assistant'
  content text not null,
  created_at timestamptz default now()
);

-- Enable Row Level Security
alter table public.chat_messages enable row level security;

-- Users can only see their own messages
create policy "Users can view own messages"
  on public.chat_messages for select
  using (auth.uid() = user_id);

-- Users can insert their own messages
create policy "Users can insert own messages"
  on public.chat_messages for insert
  with check (auth.uid() = user_id);

-- Users can delete their own messages
create policy "Users can delete own messages"
  on public.chat_messages for delete
  using (auth.uid() = user_id);


-- Mood tracker table (optional, for mood data persistence)
create table public.mood_logs (
  id bigint generated always as identity primary key,
  user_id uuid references auth.users(id) on delete cascade not null,
  log_date date not null,
  emoji text,
  score int,
  energy int,
  anxiety int,
  sleep int,
  note text,
  created_at timestamptz default now(),
  unique(user_id, log_date)
);

alter table public.mood_logs enable row level security;

create policy "Users can view own mood logs"
  on public.mood_logs for select
  using (auth.uid() = user_id);

create policy "Users can insert own mood logs"
  on public.mood_logs for insert
  with check (auth.uid() = user_id);

create policy "Users can update own mood logs"
  on public.mood_logs for update
  using (auth.uid() = user_id);
```

3. **Run** pa click karein. "Success" message aana chahiye.

---

## STEP 4: Email Authentication Enable Karein

1. Left sidebar mein **Authentication** → **Providers** pa jayein
2. **Email** provider already enabled hoga (default)
3. Agar aap chahte hain users bina email confirm kiye login kar sakein (testing ke liye asaan):
   - **Authentication** → **Settings** (ya Providers → Email settings)
   - **"Confirm email"** ko **OFF/disable** kar dein (development ke liye)
   - Production mein ise ON rakhna better hai, lekin tab users ko apna email confirm karna parega

---

## STEP 5: Project Files Setup Karein

Apne computer pa ek folder banayein, us mein ye files honi chahiye (jo neeche di gayi hain):

```
mindsense/
├── app.py
├── chat_widget.py
├── requirements.txt
└── .streamlit/
    └── secrets.toml
```

### `.streamlit/secrets.toml` mein apni keys dalein:

```toml
SUPABASE_URL = "https://xxxxx.supabase.co"
SUPABASE_KEY = "your-anon-public-key-here"
GROQ_API_KEY = "your-groq-api-key-here"
```

⚠️ **IMPORTANT**: `.streamlit/secrets.toml` file ko kabhi GitHub pa public push na karein! Ye aapki private keys hain.

---

## STEP 6: Local Testing

1. Python install hona chahiye (3.9+)
2. Terminal mein project folder pa jayein aur run karein:

```bash
pip install -r requirements.txt
streamlit run app.py
```

3. Browser mein `http://localhost:8501` khulega — signup/login test karein.

---

## STEP 7: Streamlit Cloud pa Deploy Karein (FREE)

1. Apna code GitHub pa push karein (ek **public ya private repo** banayein)
   - ⚠️ `secrets.toml` ko `.gitignore` mein add karein, GitHub pa push na karein!
2. Jayein: https://share.streamlit.io
3. GitHub se login karein
4. **"New app"** → apna repo select karein → `app.py` ko main file batayein
5. **"Advanced settings"** mein jayein → **Secrets** section mein apni `secrets.toml` ka content paste karein:

```toml
SUPABASE_URL = "https://xxxxx.supabase.co"
SUPABASE_KEY = "your-anon-public-key-here"
GROQ_API_KEY = "your-groq-api-key-here"
```

6. **Deploy** pa click karein. 2-3 minute mein aapka app live ho jayega!

---

## Kaise Kaam Karta Hai (Summary)

- **Login/Signup**: Supabase Auth handle karta hai — emails/passwords securely store hote hain
- **Chat History**: Har message Supabase `chat_messages` table mein save hota hai (user ID ke saath linked)
- **Re-login pa**: Jab user dobara login karta hai, uski purani chat history database se load ho jati hai
- **Privacy**: Row Level Security (RLS) ensure karta hai ke har user sirf apna data dekh sakta hai

---

## Free Tier Limits (Supabase)

- 500 MB database storage — ye hazaron messages ke liye kafi hai
- 50,000 monthly active users
- Unlimited API requests (within fair use)

Ye free tier chote/medium projects (FYP, demo, personal use) ke liye bilkul sufficient hai.
