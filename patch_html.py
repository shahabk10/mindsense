"""
patch_html.py
==============
Applies the Supabase chat-persistence patches to your original
MindSense HTML file, producing mindsense_ui.html for use with app.py.

Usage:
    python patch_html.py original.html
Output:
    mindsense_ui.html
"""
import sys
import re

def patch(html: str) -> str:
    # ---------------------------------------------------------------
    # 1. Add injection point + Supabase CDN script right after <head>
    # ---------------------------------------------------------------
    head_addition = '''<!--__INJECTION_POINT__-->
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/dist/umd/supabase.js"></script>
'''
    html = html.replace("<head>", "<head>\n" + head_addition, 1)

    # ---------------------------------------------------------------
    # 2. Replace addWelcomeMsg() to restore history first
    # ---------------------------------------------------------------
    old_welcome = '''function addWelcomeMsg() {
  const t = T[currentLang] || T.en;
  appendAIMsg(t.welcome, true);
  messages = [{role: 'system', content: getSystemPrompt(currentLang)}];
  conversationTurn = 0;
}'''

    new_welcome = '''function addWelcomeMsg() {
  const t = T[currentLang] || T.en;
  messages = [{role: 'system', content: getSystemPrompt(currentLang)}];
  conversationTurn = 0;

  const history = window.__MINDSENSE_CHAT_HISTORY__ || [];
  if (history.length > 0) {
    // Restore previous conversation from Supabase
    history.forEach(m => {
      if (m.role === 'user') {
        appendUserMsg(m.content, true);
        messages.push({role: 'user', content: m.content});
      } else if (m.role === 'assistant') {
        appendAIMsg(m.content, true, true);
        messages.push({role: 'assistant', content: m.content});
      }
    });
    conversationTurn = history.filter(m => m.role === 'user').length;
  } else {
    appendAIMsg(t.welcome, true, true);
  }
}'''

    html = html.replace(old_welcome, new_welcome, 1)

    # ---------------------------------------------------------------
    # 3. Update appendUserMsg signature to accept "skipSave" flag
    #    and call saveMessageToSupabase when not skipped
    # ---------------------------------------------------------------
    old_append_user = '''function appendUserMsg(text) {
  const box = document.getElementById('chat-messages');
  if (!box) return;
  const div = document.createElement('div');
  div.className = 'msg-row user';
  div.innerHTML = `
    <div class="msg-avatar user">👤</div>
    <div class="msg-bubble user">${escapeHtml(text).replace(/\\n/g, '<br>')}</div>
  `;
  box.appendChild(div);
  scrollChat();
}'''

    new_append_user = '''function appendUserMsg(text, skipSave) {
  const box = document.getElementById('chat-messages');
  if (!box) return;
  const div = document.createElement('div');
  div.className = 'msg-row user';
  div.innerHTML = `
    <div class="msg-avatar user">👤</div>
    <div class="msg-bubble user">${escapeHtml(text).replace(/\\n/g, '<br>')}</div>
  `;
  box.appendChild(div);
  scrollChat();
  if (!skipSave) saveMessageToSupabase('user', text);
}'''

    html = html.replace(old_append_user, new_append_user, 1)

    # ---------------------------------------------------------------
    # 4. Update appendAIMsg signature to accept "skipSave" flag
    #    and call saveMessageToSupabase when not skipped
    # ---------------------------------------------------------------
    old_append_ai = '''function appendAIMsg(text, withActions) {
  const box = document.getElementById('chat-messages');
  if (!box) return;
  const div = document.createElement('div');
  div.className = 'msg-row';
  const formatted = formatMsg(text);
  let actions = '';
  if (withActions) {
    const safeText = JSON.stringify(text).replace(/"/g, '&quot;');
    actions = `<div class="msg-actions">
      <button class="msg-act-btn" onclick="speakText(${safeText})" id="listen-btn-${Date.now()}">🔊 Listen</button>
      <button class="msg-act-btn" onclick="stopSpeaking()" style="background:rgba(220,38,38,0.1);color:#dc2626;border-color:rgba(220,38,38,0.3)">⏹ Stop</button>
      <button class="msg-act-btn" onclick="copyText(${safeText})">📋 Copy</button>
    </div>`;
  }
  div.innerHTML = `
    <div class="msg-avatar ai">🧠</div>
    <div class="msg-bubble ai">${formatted}${actions}</div>
  `;
  box.appendChild(div);
  scrollChat();

  // Auto-speak if enabled
  if (withActions && settings.autoVoice) {
    speakText(text);
  }
}'''

    new_append_ai = '''function appendAIMsg(text, withActions, skipSave) {
  const box = document.getElementById('chat-messages');
  if (!box) return;
  const div = document.createElement('div');
  div.className = 'msg-row';
  const formatted = formatMsg(text);
  let actions = '';
  if (withActions) {
    const safeText = JSON.stringify(text).replace(/"/g, '&quot;');
    actions = `<div class="msg-actions">
      <button class="msg-act-btn" onclick="speakText(${safeText})" id="listen-btn-${Date.now()}">🔊 Listen</button>
      <button class="msg-act-btn" onclick="stopSpeaking()" style="background:rgba(220,38,38,0.1);color:#dc2626;border-color:rgba(220,38,38,0.3)">⏹ Stop</button>
      <button class="msg-act-btn" onclick="copyText(${safeText})">📋 Copy</button>
    </div>`;
  }
  div.innerHTML = `
    <div class="msg-avatar ai">🧠</div>
    <div class="msg-bubble ai">${formatted}${actions}</div>
  `;
  box.appendChild(div);
  scrollChat();

  // Auto-speak if enabled
  if (withActions && settings.autoVoice) {
    speakText(text);
  }
  if (!skipSave) saveMessageToSupabase('assistant', text);
}'''

    html = html.replace(old_append_ai, new_append_ai, 1)

    # ---------------------------------------------------------------
    # 5. Update resetConversation/clearConversation to also clear
    #    Supabase history when user clicks "Clear Conversation"
    # ---------------------------------------------------------------
    old_clear = '''function clearConversation() {
  if (!confirm('Clear the conversation?')) return;
  resetConversation();
}'''

    new_clear = '''function clearConversation() {
  if (!confirm('Clear the conversation? This will also delete your saved chat history.')) return;
  clearSupabaseHistory();
  resetConversation();
}'''

    html = html.replace(old_clear, new_clear, 1)

    # Also fix resetConversation to not duplicate-save the welcome message
    old_reset = '''function resetConversation() {
  const box = document.getElementById('chat-messages');
  if (box) box.innerHTML = '';
  messages = [{role: 'system', content: getSystemPrompt(currentLang)}];
  conversationTurn = 0;
  addWelcomeMsg();
}'''

    new_reset = '''function resetConversation() {
  const box = document.getElementById('chat-messages');
  if (box) box.innerHTML = '';
  messages = [{role: 'system', content: getSystemPrompt(currentLang)}];
  conversationTurn = 0;
  const t = T[currentLang] || T.en;
  appendAIMsg(t.welcome, true, true);
}'''

    html = html.replace(old_reset, new_reset, 1)

    # ---------------------------------------------------------------
    # 6. Add the Supabase bridge functions just before </script> of
    #    the LAST script block (end of file)
    # ---------------------------------------------------------------
    bridge_js = '''

// ============================================================
// SUPABASE CHAT PERSISTENCE BRIDGE
// ============================================================
let __sbClient = null;
try {
  if (window.supabase && window.__MINDSENSE_SUPABASE_URL__ && window.__MINDSENSE_SUPABASE_KEY__) {
    __sbClient = window.supabase.createClient(
      window.__MINDSENSE_SUPABASE_URL__,
      window.__MINDSENSE_SUPABASE_KEY__,
      {
        auth: { persistSession: false }
      }
    );
    // Attach the logged-in user's session so RLS policies recognize them
    if (window.__MINDSENSE_ACCESS_TOKEN__) {
      __sbClient.auth.setSession({
        access_token: window.__MINDSENSE_ACCESS_TOKEN__,
        refresh_token: window.__MINDSENSE_ACCESS_TOKEN__
      }).catch(() => {});
    }
  }
} catch (e) {
  console.warn('Supabase client init failed:', e);
}

function saveMessageToSupabase(role, content) {
  if (!__sbClient || !window.__MINDSENSE_USER_ID__) return;
  __sbClient.from('chat_messages').insert({
    user_id: window.__MINDSENSE_USER_ID__,
    role: role,
    content: content
  }).then(({error}) => {
    if (error) console.warn('Supabase save error:', error.message);
  });
}

function clearSupabaseHistory() {
  if (!__sbClient || !window.__MINDSENSE_USER_ID__) return;
  __sbClient.from('chat_messages')
    .delete()
    .eq('user_id', window.__MINDSENSE_USER_ID__)
    .then(({error}) => {
      if (error) console.warn('Supabase clear error:', error.message);
    });
}
'''

    # Insert before the very last </script> tag in the file
    last_script_idx = html.rfind("</script>")
    html = html[:last_script_idx] + bridge_js + "\n" + html[last_script_idx:]

    return html


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python patch_html.py original.html")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        original = f.read()

    patched = patch(original)

    with open("mindsense_ui.html", "w", encoding="utf-8") as f:
        f.write(patched)

    print("Done! Created mindsense_ui.html")
