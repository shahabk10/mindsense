# MindSense — Streamlit Edition (Login + Persistent Chat)

Ye package aapke original MindSense HTML project ko **Streamlit** mein
deploy karne ke liye ready karta hai, with:

- ✅ **Login / Signup** (Supabase Auth — free)
- ✅ **Chat history save hoti hai** — re-login pe wapas mil jati hai
- ✅ Aapka design, animations, AI logic, sab kuch **wahi rehta hai** (kuch nahi badla)
- ✅ Free deployment Streamlit Cloud pe

---

## Files

```
mindsense/
├── app.py                  ← Streamlit entry point (login/signup + embed)
├── patch_html.py           ← Aapki original HTML ko auto-patch karta hai
├── mindsense_ui.html        ← (aap generate karenge — Step 2)
├── requirements.txt
├── SETUP_GUIDE.md           ← Supabase setup ki detailed guide
└── .streamlit/
    └── secrets.toml.example
```

---

## QUICK START (3 Steps)

### Step 1 — Supabase Setup
`SETUP_GUIDE.md` file kholein aur Steps 1-4 follow karein:
- Free Supabase account banayein
- Database table (`chat_messages`) create karein (SQL diya gaya hai)
- Email auth enable karein
- `SUPABASE_URL` aur `SUPABASE_KEY` copy kar lein

### Step 2 — Apni HTML File Patch Karein

Apni original HTML file (jo aap currently use kar rahe hain) is folder mein
`original.html` naam se save karein, phir terminal mein:

```bash
python patch_html.py original.html
```

Ye automatically `mindsense_ui.html` bana dega — jis mein:
- Supabase JS client add hota hai
- Chat history restore hone ka logic add hota hai
- Har message automatically Supabase mein save hone ka code add hota hai

**Aapki design, animations, AI chat logic — kuch bhi nahi badla.** Sirf
6 chote functions mein chat-saving ke 1-2 extra lines add hue hain.

### Step 3 — Secrets Set Karein aur Run Karein

`.streamlit/secrets.toml.example` ko `.streamlit/secrets.toml` rename karke
apni real keys dalein:

```toml
SUPABASE_URL = "https://xxxxx.supabase.co"
SUPABASE_KEY = "your-anon-public-key"
GROQ_API_KEY = "your-groq-api-key"
```

Phir:

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Kya Hua Hai Code Mein (Technical Summary)

### `app.py`
- Supabase client initialize karta hai
- Login/Signup forms dikhata hai (Streamlit native UI)
- Login ke baad, user ki **chat history database se fetch** karta hai
- `mindsense_ui.html` ko ek iframe mein render karta hai, aur usmein
  inject karta hai:
  - `window.__MINDSENSE_USER_ID__` — current user ka ID
  - `window.__MINDSENSE_CHAT_HISTORY__` — pichli saari messages
  - `window.__MINDSENSE_SUPABASE_URL__` / `KEY` / `ACCESS_TOKEN__` — taake
    HTML khud Supabase se baat kar sake
  - `window.__MINDSENSE_GROQ_KEY__` — aapka Groq API key

### `patch_html.py` — 6 Patches
1. `<head>` mein Supabase JS CDN script + injection point add karta hai
2. `addWelcomeMsg()` — ab pehle check karta hai ke history hai ya nahi.
   Agar hai, to puraani conversation restore karta hai. Agar nahi, to
   normal welcome message dikhata hai.
3. `appendUserMsg()` — har user message ko `saveMessageToSupabase()` call
   karke save karta hai (jab tak history-restore mode mein na ho)
4. `appendAIMsg()` — same, AI ke replies ke liye
5. `clearConversation()` — ab Supabase se bhi history delete karta hai
6. File ke end mein Supabase bridge functions add karta hai:
   - `saveMessageToSupabase(role, content)`
   - `clearSupabaseHistory()`

---

## Deployment (Streamlit Cloud — FREE)

`SETUP_GUIDE.md` ka **Step 7** follow karein. Summary:

1. GitHub repo banayein, code push karein (secrets.toml push NA karein!)
2. https://share.streamlit.io pe jayein → New App → repo select karein
3. Advanced Settings → Secrets mein apni keys paste karein
4. Deploy!

---

## Important Notes

- **Privacy**: Har user ka data Row-Level-Security (RLS) se protected hai —
  koi doosre ka data nahi dekh sakta.
- **Free Limits**: Supabase free tier 500MB storage + 50,000 monthly users
  deta hai — chote/medium projects ke liye kaafi hai.
- **Email Confirmation**: Testing ke liye Supabase dashboard mein
  "Confirm email" ko OFF kar dein (Authentication → Settings), warna
  signup ke baad user ko email verify karna parega.
- **Groq API Key**: Aapki existing key already hardcoded thi original
  file mein — ab ye secrets.toml se aati hai (zyada secure). Agar aap
  chahte hain ke wahi hardcoded key chale, to `mindsense_ui.html` mein
  `GROQ_API_KEY` variable ko `window.__MINDSENSE_GROQ_KEY__ || "gsk_..."`
  se replace kar sakte hain.
