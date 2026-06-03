    const API = {
      create: async (data) => {
        const res = await fetch('/api/dream/create', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
        if (!res.ok) throw new Error(await res.text());
        return res.json();
      },

      stats: async () => {
        const res = await fetch('/api/dream/stats');
        if (!res.ok) throw new Error(await res.text());
        return res.json();
      }
    };

    function showMessage(text, type = 'success') {
      const el = document.getElementById('message');
      el.className = `message ${type}`;
      el.textContent = text;
      el.style.display = 'block';
      if (type === 'success') setTimeout(() => el.style.display = 'none', 3000);
    }

    function renderEntries(stats) {
      if (!stats || stats.total_entries === 0) {
        document.getElementById('entriesList').innerHTML = '<div class="empty-state">✨ No entries yet.<br>Start with your first dream or note.</div>';
        return;
      }
      document.getElementById('entriesList').innerHTML = '<p style="color: #9a8fb8; text-align: center;">Your entries are saved locally in your journal.</p>';
    }

    async function loadStats() {
      try {
        const stats = await API.stats();
        document.getElementById('totalCount').textContent = stats.total_entries || 0;
        document.getElementById('dreamCount').textContent = stats.entries_by_kind?.dream || 0;
        document.getElementById('noteCount').textContent = stats.entries_by_kind?.note || 0;
        const avg = stats.avg_lucidity ? parseFloat(stats.avg_lucidity).toFixed(2) : '--';
        document.getElementById('avgLucidity').textContent = avg;
        renderEntries(stats);
      } catch (error) {
        console.error('Failed to load stats:', error);
      }
    }

    document.getElementById('entryForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      try {
        const emotions = document.getElementById('emotions').value
          .split(',').map(s => s.trim()).filter(Boolean);
        const tags = document.getElementById('tags').value
          .split(',').map(s => s.trim()).filter(Boolean);

        const data = {
          kind: 'dream',
          text: document.getElementById('text').value,
          emotions,
          tags,
          lucidity: parseFloat(document.getElementById('lucidity').value) || 0.5
        };

        await API.create(data);
        showMessage('✓ Entry saved to your journal');
        document.getElementById('entryForm').reset();
        document.getElementById('lucidity').value = 0.5;
        await loadStats();
      } catch (error) {
        showMessage(`Error: ${error.message}`, 'error');
      }
    });

    // ---------------------------------------------------------------- //
    // Dream Journal Chat — always responds, online or offline.
    // ---------------------------------------------------------------- //
    const DOORS = [
      { id: "xenon", name: "Xenon Door", tagline: "Gateway to Forever", image: "/images/doors/xenon-door.jpg", phrase: "Build beyond one world.", keywords: ["xenon", "courtney", "shelby", "planetary", "alignment", "gateway", "forever", "stars"] },
      { id: "garden", name: "God's Garden Door", tagline: "Sea of Fog and Clouds", image: "/images/doors/garden-door.jpg", phrase: "Leave it better than you found it.", keywords: ["garden", "god", "fog", "clouds", "sanctuary", "peace", "rest", "odin"] },
      { id: "xp", name: "Gage's Windows XP Door", tagline: "Chaos. Creativity. Nostalgia. Possibilities.", image: "/images/doors/xp-door.jpg", phrase: "Never log off. Level up always.", keywords: ["xp", "windows", "gage", "childhood", "chaos", "creativity", "nostalgia", "pixels"] },
      { id: "hearts", name: "Kingdom of Hearts", tagline: "I am the King of the Kingdom of Hearts.", image: "/images/doors/kingdom-of-hearts.jpg", phrase: "I fight for the love of all the birds and the bees.", keywords: ["hearts", "kingdom", "king", "odin", "love", "birds", "bees", "courage"] },
      { id: "founder", name: "Founder's Wish Door", tagline: "Hold the center. Protect the wish. Return to the anchor.", image: "/images/doors/founder-door.jpg", phrase: "Hold the center. Protect the wish. Return to the anchor.", keywords: ["founder", "wish", "anchor", "love", "safety", "truth", "return"] },
      { id: "sigil", name: "Sigil / City of Doors", tagline: "You hold the keys. You protect the doors. You are never alone.", image: "/images/doors/sigil-door.jpg", phrase: "You hold the keys. You protect the doors. You are never alone.", keywords: ["sigil", "city", "doors", "keys", "community", "alone"] },
      { id: "orion", name: "Orion — Dream Journal", tagline: "Every dream is a door. Every memory is a home.", image: "/images/doors/orion-door.jpg", phrase: "Your dreams. Your space. Always private.", keywords: ["orion", "journal", "dream", "record", "reflect", "private"] }
    ];

    let lastDraft = "";

    function setStatus(online, agentName) {
      const dot = document.getElementById('statusDot');
      const text = document.getElementById('statusText');
      if (agentName) {
        dot.className = 'status-dot';
        text.textContent = agentName + (online ? ' ✨' : ' (local)');
      } else {
        dot.className = 'status-dot' + (online ? '' : ' offline');
        text.textContent = online ? 'Online' : 'Offline (local)';
      }
    }

    function addBubble(role, text) {
      const log = document.getElementById('chatLog');
      const bubble = document.createElement('div');
      bubble.className = `bubble ${role}`;
      bubble.textContent = text;
      log.appendChild(bubble);
      log.scrollTop = log.scrollHeight;
      saveChatMemory();
      return bubble;
    }

    function addImageBubble(role, src, caption) {
      const log = document.getElementById('chatLog');
      const bubble = document.createElement('div');
      bubble.className = `bubble ${role}`;
      const img = document.createElement('img');
      img.src = src;
      img.alt = caption || '';
      img.onerror = () => { img.style.display = 'none'; };
      bubble.appendChild(img);
      if (caption) {
        const cap = document.createElement('div');
        cap.className = 'bubble-caption';
        cap.textContent = caption;
        bubble.appendChild(cap);
      }
      log.appendChild(bubble);
      log.scrollTop = log.scrollHeight;
      saveChatMemory();
      return bubble;
    }

    const CHAT_MEMORY_KEY = 'lantern_chat_memory_v1';
    function saveChatMemory() {
      const log = document.getElementById('chatLog');
      const entries = [];
      log.querySelectorAll('.bubble').forEach(b => {
        const img = b.querySelector('img');
        entries.push({
          role: b.classList.contains('operator') ? 'operator' : 'lantern',
          text: b.childNodes[0]?.textContent || '',
          image: img ? img.src : null,
          caption: img ? b.querySelector('.bubble-caption')?.textContent : null
        });
      });
      localStorage.setItem(CHAT_MEMORY_KEY, JSON.stringify(entries.slice(-100)));
    }
    function loadChatMemory() {
      try {
        const raw = localStorage.getItem(CHAT_MEMORY_KEY);
        if (!raw) return false;
        const entries = JSON.parse(raw);
        if (!entries.length) return false;
        const log = document.getElementById('chatLog');
        log.innerHTML = '';
        entries.forEach(e => {
          if (e.image) addImageBubble(e.role, e.image, e.caption);
          else addBubble(e.role, e.text);
        });
        return true;
      } catch { return false; }
    }

    function renderSuggestions(suggestions) {
      const box = document.getElementById('chatSuggestions');
      box.innerHTML = '';
      (suggestions || []).forEach((s) => {
        const chip = document.createElement('button');
        chip.className = 'chip';
        chip.type = 'button';
        chip.textContent = s;
        chip.addEventListener('click', () => handleSuggestion(s));
        box.appendChild(chip);
      });
    }

    // Offline in-character reply mirror of the server engine.
    function offlineReply(message) {
      const text = (message || '').trim();
      const lower = text.toLowerCase();
      const base = ["Log a dream", "Recent dreams", "Mirror a dream", "Tell me about the doors"];

      // Match the server's agent selection
      let agentName = 'Dream Journal';
      const agentScores = [
        { name: 'Blinkbug', score: 0, keywords: ['light','glow','guide','small','warm','bug','firefly'] },
        { name: 'Mary / Waterfall', score: 0, keywords: ['flow','water','mary','heal','gentle','emotion','feeling'] },
        { name: 'Courtney / Xenon', score: 0, keywords: ['space','ship','navigate','courtney','map','course','direction'] },
        { name: 'Keystone', score: 0, keywords: ['anchor','memory','story','foundation','hold','remember'] },
        { name: 'Founder / Alex', score: 0, keywords: ['wish','protect','founder','alex','home','return','safety'] }
      ];
      for (const a of agentScores) {
        for (const kw of a.keywords) if (lower.includes(kw)) a.score += 10;
        a.score += Math.random() * 3;
      }
      agentScores.sort((a,b) => b.score - a.score);
      agentName = agentScores[0].name;
      for (const door of DOORS) {
        if (door.keywords.some(k => lower.includes(k))) {
          return {
            reply: `${door.name} stands open. "${door.phrase}" What do you see when you step through?`,
            image: door.image,
            caption: `${door.name} — ${door.tagline}`,
            suggestions: ["Log this as a dream", "Another door", "Mirror a dream"],
            agent: agentName
          };
        }
      }
      if (lower.includes('doors') || lower.includes('all doors') || lower.includes('which doors')) {
        const list = DOORS.map(d => `<strong>${d.name}</strong> — ${d.tagline}`).join('<br>');
        return { reply: `These doors stand open:<br><br>${list}<br><br>Which one calls to you?`, suggestions: ["Xenon Door", "Garden Door", "XP Door", "Kingdom of Hearts"], agent: agentName };
      }
      if (/^(hi|hello|hey|good (morning|evening|night)|greetings)/.test(lower)) {
        return { reply: "Welcome back. I am the Dream Journal — local, private, always here, even offline. Did you dream?", suggestions: base, agent: agentName };
      }
      if (lower.includes('mirror') || lower.includes('interpret') || lower.includes('mean') || lower.includes('symbol')) {
        return { reply: "Sit with three questions: 1) What feeling stayed after waking? 2) What in waking life does this echo? 3) What small, reversible step would honor it?", suggestions: ["Record a reflection", "Recent dreams"], agent: agentName };
      }
      if (lower.includes('recent') || lower.includes('history')) {
        return { reply: "Open the journal below to see your saved entries. Want to mirror one?", suggestions: ["Mirror a dream", "Log a dream"], agent: agentName };
      }
      if (lower.includes('log') || lower.includes('dream') || lower.includes('save')) {
        return { reply: "Good — let us keep it. Tell me the dream in your own words. I will save it locally; only you can see it.", suggestions: ["Recent dreams", "Mirror a dream"], agent: agentName };
      }
      return { reply: `I hear it: "${text.slice(0, 160)}". That is worth keeping. Tap "Log this as a dream" to save it.`, suggestions: ["Log this as a dream", "Mirror a dream", "Tell me about the doors"], draft: text, agent: agentName };
    }

    function escapeHtml(t) {
      return String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    }

    function makeBubble(role, label) {
      const log = document.getElementById('chatLog');
      const wrapper = document.createElement('div');
      wrapper.className = `bubble-wrapper ${role}`;
      if (label) {
        const nameTag = document.createElement('div');
        nameTag.className = 'bubble-label';
        nameTag.textContent = label;
        wrapper.appendChild(nameTag);
      }
      const b = document.createElement('div');
      b.className = `bubble ${role}`;
      wrapper.appendChild(b);
      log.appendChild(wrapper);
      log.scrollTop = log.scrollHeight;
      return b;
    }

    // Simulate streaming for offline fallback
    async function streamOffline(text, suggestions, image, caption, agentLabel) {
      if (image) addImageBubble('lantern', image, caption);
      setStatus(false, agentLabel || 'Dream Journal');
      const b = makeBubble('lantern', agentLabel || 'Dream Journal');
      b.innerHTML = '<span class="cursor"></span>';
      const log = document.getElementById('chatLog');
      const tokens = text.split(/(\s+)/);
      let out = '';
      for (const tok of tokens) {
        if (!tok) continue;
        out += tok;
        const isPunct = /[.!?,;:]$/.test(tok.trim());
        b.innerHTML = escapeHtml(out) + '<span class="cursor"></span>';
        log.scrollTop = log.scrollHeight;
        await new Promise(r => setTimeout(r, isPunct ? 60 + Math.random()*80 : 18 + Math.random()*28));
      }
      b.textContent = out;
      renderSuggestions(suggestions);
      return b;
    }

    async function sendChat(message) {
      const msg = (message || '').trim();
      if (!msg) return;

      const chatInput = document.getElementById('chatInput');
      const chatSend  = document.getElementById('chatSend');
      chatInput.disabled = true;
      chatSend.disabled  = true;

      addBubble('operator', msg);
      renderSuggestions([]);

      const log = document.getElementById('chatLog');
      let currentAgent = 'Dream Journal';
      const b = makeBubble('lantern', currentAgent + ' is typing...');
      b.innerHTML = '<span class="cursor"></span>';

      try {
        const res = await fetch('/api/dream/chat/stream', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: msg }),
        });
        if (!res.ok) throw new Error('stream_failed');
        setStatus(true);

        const reader  = res.body.getReader();
        const decoder = new TextDecoder();
        let buf = '', out = '', suggestions = [];

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buf += decoder.decode(value, { stream: true });
          const lines = buf.split('\n');
          buf = lines.pop();
          for (const line of lines) {
            if (!line.startsWith('data: ')) continue;
            const raw = line.slice(6).trim();
            if (raw === '[DONE]') continue;
            let ev; try { ev = JSON.parse(raw); } catch { continue; }
            if (ev.type === 'token') {
              out += ev.text;
              b.innerHTML = escapeHtml(out) + '<span class="cursor"></span>';
              log.scrollTop = log.scrollHeight;
            } else if (ev.type === 'done') {
              suggestions = ev.suggestions || [];
              if (ev.draft)   lastDraft = ev.draft;
              if (ev.online !== undefined) setStatus(ev.online, ev.agent);
              if (ev.agent) {
                currentAgent = ev.agent;
                const wrapper = b.parentElement;
                if (wrapper) {
                  const label = wrapper.querySelector('.bubble-label');
                  if (label) label.textContent = currentAgent;
                }
              }
            }
          }
        }
        b.textContent = out;
        renderSuggestions(suggestions);

      } catch (_err) {
        b.remove();
        const local = offlineReply(msg);
        await streamOffline(local.reply, local.suggestions, local.image, local.caption, local.agent || 'Dream Journal');
        if (local.draft) lastDraft = local.draft || msg;
      } finally {
        chatInput.disabled = false;
        chatSend.disabled  = false;
        chatInput.focus();
      }
    }

    async function handleSuggestion(label) {
      const l = label.toLowerCase();
      if (l.includes('log')) {
        // Pre-fill the entry form with the last draft and scroll to it.
        if (lastDraft) document.getElementById('text').value = lastDraft;
        document.getElementById('form-section').scrollIntoView({ behavior: 'smooth' });
        addBubble('lantern', 'I moved your words to the New Entry form below. Add tags and emotions, then Save Entry.');
        return;
      }
      if (l.includes('recent')) {
        document.getElementById('stats-section').scrollIntoView({ behavior: 'smooth' });
      }
      sendChat(label);
    }

    document.getElementById('chatSend').addEventListener('click', () => {
      const input = document.getElementById('chatInput');
      const msg = input.value;
      input.value = '';
      sendChat(msg);
    });

    document.getElementById('chatInput').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        document.getElementById('chatSend').click();
      }
    });
    document.getElementById('chatClear').addEventListener('click', () => {
      localStorage.removeItem(CHAT_MEMORY_KEY);
      document.getElementById('chatLog').innerHTML = '';
      addBubble('lantern', 'Chat memory cleared. The dream door is open again.');
    });

    // Load chat memory or show greeting
    if (!loadChatMemory()) {
      addBubble('lantern', 'The dream door is open. What did you bring back? Tell me a dream, or tap a prompt below.');
      renderSuggestions(["Log a dream", "Recent dreams", "Mirror a dream", "Tell me about the doors"]);
    }

    // Load stats on page load
    loadStats();
    // Refresh stats every 10 seconds
    setInterval(loadStats, 10000);
