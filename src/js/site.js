(function () {
  var CFG = window.MY_CONFIG || {};
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };

  var year = document.getElementById('year');
  if (year) year.textContent = new Date().getFullYear();

  // Legacy single-page anchors (mindyards.in/#agentic etc.) forward to the new page URLs.
  if (window.MY_LEGACY && location.hash) {
    var legacy = window.MY_LEGACY[location.hash.slice(1)];
    if (legacy) { location.replace(legacy); return; }
  }

  var btn = document.getElementById('menuBtn'), nav = document.getElementById('nav');
  if (btn && nav) {
    btn.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      btn.setAttribute('aria-expanded', open);
    });
  }

  // Mark the current page in the header navigation.
  var path = location.pathname.replace(/index\.html$/, '');
  if (nav) {
    $$('a', nav).forEach(function (a) {
      var href = a.getAttribute('href') || '';
      if (href.charAt(0) !== '/') return;
      var p = href.split('#')[0].split('?')[0];
      if (!p || p === '/') return;
      if (path === p) a.classList.add('on');
      else if (a.parentNode.classList.contains('dd') && path.indexOf(p) === 0) a.classList.add('on');
    });
  }

  // ---------------------------------------------------------------- motion
  // Keep in sync with the html.js selector list in site.css.
  var REVEAL = '.ov article,.ind article,.sol article,.eng article,.cap,.step,.stack > div,.sec-head,.line .intro,.facts > div,.faq details,.strip .wrap > div,.expect,.contact form,.about .photo,.quote,.focus,.incl,.cmp-wrap,.posts article,.est .panel,.chk fieldset,.estcta .wrap > *,.post .body > *,.related article';
  var targets = $$(REVEAL);
  if (!('IntersectionObserver' in window) || reduce) {
    targets.forEach(function (el) { el.classList.add('in', 'done'); });
  } else {
    var groups = new Map();
    targets.forEach(function (el) {
      el.classList.add('rv');
      var p = el.parentNode, n = groups.get(p) || 0;
      groups.set(p, n + 1);
      el.style.transitionDelay = (Math.min(n, 5) * 70) + 'ms';
    });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        var el = e.target;
        el.classList.add('in');
        io.unobserve(el);
        setTimeout(function () { el.classList.add('done'); el.style.transitionDelay = ''; }, 1200);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    targets.forEach(function (el) { io.observe(el); });
  }

  // Count-up numbers in the stat strip.
  var counters = $$('[data-count]');
  if (counters.length) {
    var runCount = function (el) {
      var end = parseFloat(el.getAttribute('data-count')), suffix = el.getAttribute('data-suffix') || '';
      if (reduce || !('IntersectionObserver' in window)) { el.textContent = end + suffix; return; }
      var t0 = null, dur = 1300;
      var step = function (t) {
        if (!t0) t0 = t;
        var k = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - k, 3);
        el.textContent = Math.round(end * e) + suffix;
        if (k < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    };
    if (reduce || !('IntersectionObserver' in window)) counters.forEach(runCount);
    else {
      var cio = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) { if (e.isIntersecting) { runCount(e.target); cio.unobserve(e.target); } });
      }, { threshold: 0.4 });
      counters.forEach(function (el) { cio.observe(el); });
    }
  }

  // Parallax drift on page banners (desktop only).
  var banners = $$('.banner img');
  if (banners.length && !reduce && window.innerWidth > 900) {
    banners.forEach(function (im) { im.classList.add('px'); });
    var ticking = false;
    var drift = function () {
      ticking = false;
      var vh = window.innerHeight;
      banners.forEach(function (im) {
        var r = im.parentNode.getBoundingClientRect();
        if (r.bottom < 0 || r.top > vh) return;
        var k = (r.top + r.height / 2 - vh / 2) / vh; // -1 .. 1
        im.style.transform = 'translateY(' + (k * 6).toFixed(2) + '%)';
      });
    };
    window.addEventListener('scroll', function () { if (!ticking) { ticking = true; requestAnimationFrame(drift); } }, { passive: true });
    drift();
  }

  // ---------------------------------------------------------------- booking (Calendly) and floating buttons
  var calendly = CFG.calendly;
  if (calendly) {
    var calLoaded = false;
    var loadCal = function (cb) {
      if (window.Calendly) return cb();
      if (!calLoaded) {
        calLoaded = true;
        var l = document.createElement('link'); l.rel = 'stylesheet'; l.href = 'https://assets.calendly.com/assets/external/widget.css'; document.head.appendChild(l);
        var s = document.createElement('script'); s.src = 'https://assets.calendly.com/assets/external/widget.js'; s.async = true; document.head.appendChild(s);
      }
      var tries = 0, w = setInterval(function () { if (window.Calendly || ++tries > 50) { clearInterval(w); cb(); } }, 100);
    };
    $$('a.book').forEach(function (a) {
      a.addEventListener('click', function (e) {
        e.preventDefault();
        loadCal(function () {
          if (window.Calendly) window.Calendly.initPopupWidget({ url: calendly });
          else location.href = a.href;
        });
      });
    });
    var expect = $('.contact .expect');
    if (expect) {
      var cal = document.createElement('div');
      cal.className = 'cal';
      cal.innerHTML = '<div class="hd">Prefer to pick a time now?</div><iframe title="Book a discovery call" loading="lazy" src="' + esc(calendly) + (calendly.indexOf('?') > -1 ? '&' : '?') + 'hide_gdpr_banner=1&background_color=ffffff&primary_color=f26a1b"></iframe>';
      expect.parentNode.insertBefore(cal, expect.nextSibling);
    }
  }

  var floatBox = null;
  var getFloat = function () {
    if (!floatBox) { floatBox = document.createElement('div'); floatBox.className = 'float'; document.body.appendChild(floatBox); }
    return floatBox;
  };
  if (CFG.whatsapp) {
    var num = String(CFG.whatsapp).replace(/\D/g, '');
    var wa = document.createElement('a');
    wa.className = 'wa'; wa.target = '_blank'; wa.rel = 'noopener';
    wa.href = 'https://wa.me/' + num + '?text=' + encodeURIComponent('Hi MindYards, I found you on ' + location.href + ' and would like to talk about ');
    wa.setAttribute('aria-label', 'Chat on WhatsApp');
    wa.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 20l1.3-3.9A8 8 0 1 1 8 19.1L4 20z"/><path d="M9 9.5c0 3 2.5 5.5 5.5 5.5l1-1.5-2-1-1 1a4 4 0 0 1-2-2l1-1-1-2z"/></svg><span>WhatsApp</span>';
    getFloat().appendChild(wa);
    var details = $('.contact .details');
    if (details) {
      var li = document.createElement('li');
      li.innerHTML = '<span class="ic"><svg viewBox="0 0 24 24"><path d="M4 20l1.3-3.9A8 8 0 1 1 8 19.1L4 20z"/></svg></span><span class="val"><a href="' + wa.href + '" target="_blank" rel="noopener">Chat on WhatsApp</a></span>';
      details.insertBefore(li, details.children[1] || null);
    }
  }

  // ---------------------------------------------------------------- forms (Web3Forms when a key is configured, else mailto)
  var postForm = function (fields, onOk, onErr) {
    fields.access_key = CFG.formKey;
    fields.from_name = 'mindyards.in';
    var ctrl = new AbortController(), t = setTimeout(function () { ctrl.abort(); }, 15000);
    fetch('https://api.web3forms.com/submit', {
      method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(fields), signal: ctrl.signal
    }).then(function (r) { return r.json(); }).then(function (j) {
      clearTimeout(t);
      if (j && j.success) onOk(); else onErr();
    }).catch(function () { clearTimeout(t); onErr(); });
  };
  var setStatus = function (host, cls, msg) {
    var s = $('.status', host);
    if (!s) { s = document.createElement('p'); s.className = 'status'; host.appendChild(s); }
    s.className = 'status ' + cls; s.textContent = msg;
  };

  var form = document.getElementById('contactForm');
  if (form) {
    var topic = null, estNote = null;
    try { var q = new URLSearchParams(location.search); topic = q.get('topic'); estNote = q.get('est'); } catch (e) {}
    var topics = window.MY_TOPICS || {};
    var sel = document.getElementById('service');
    var from = topic && topics[topic] ? topics[topic] : null;
    if (from && sel) {
      $$('option', sel).forEach(function (o) { if (o.text === from[0]) sel.value = o.value || o.text; });
    }
    var msgEl = document.getElementById('msg');
    if (estNote && msgEl && !msgEl.value) msgEl.value = 'From the estimator: ' + estNote.slice(0, 400) + '\n\n';
    var note = $('.note', form);
    if (CFG.formKey && note) note.textContent = 'Sent straight to our inbox. We reply within two working days.';
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var v = function (id) { return (document.getElementById(id).value || '').trim(); };
      var service = v('service') || 'Not sure yet';
      var subject = 'MindYards enquiry: ' + (from ? from[1] : service) + (v('company') ? ' (' + v('company') + ')' : '');
      if (CFG.formKey) {
        var hp = $('input[name="botcheck"]', form);
        if (hp && hp.checked) return;
        var b = $('button[type=submit]', form); b.disabled = true;
        postForm({ subject: subject, name: v('name'), email: v('email'), company: v('company') || '-', interested_in: service,
                   regarding: from ? from[1] : '-', page: location.href, message: v('msg') },
          function () { b.disabled = false; form.reset(); setStatus(form, 'ok', 'Thank you. Your message is in our inbox and we will reply within two working days.'); },
          function () { b.disabled = false; setStatus(form, 'err', 'That did not go through. Please email contact@mindyards.in directly.'); });
        return;
      }
      var body = 'Name: ' + v('name') + '\n' +
                 'Email: ' + v('email') + '\n' +
                 'Company: ' + (v('company') || '-') + '\n' +
                 'Interested in: ' + service + '\n' +
                 (from ? 'Regarding: ' + from[1] + '\n' : '') + '\n' +
                 v('msg') + '\n';
      window.location.href = 'mailto:contact@mindyards.in?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
    });
  }

  var news = document.getElementById('newsForm');
  if (news) {
    news.addEventListener('submit', function (e) {
      e.preventDefault();
      var em = ($('input[type=email]', news).value || '').trim();
      if (!em) return;
      if (CFG.formKey) {
        var b = $('button', news); b.disabled = true;
        postForm({ subject: 'Newsletter signup: ' + em, email: em, page: location.href, message: 'Please add me to the MindYards monthly note.' },
          function () { b.disabled = false; news.reset(); setStatus(news.parentNode, 'ok', 'You are on the list. One email a month, unsubscribe any time.'); },
          function () { b.disabled = false; setStatus(news.parentNode, 'err', 'That did not go through. Email contact@mindyards.in and we will add you.'); });
      } else {
        location.href = 'mailto:contact@mindyards.in?subject=' + encodeURIComponent('Subscribe me to the monthly note') + '&body=' + encodeURIComponent('Please add ' + em + ' to the MindYards monthly note.');
      }
    });
  }

  // ---------------------------------------------------------------- estimator
  var est = document.getElementById('est');
  if (est) {
    var el = function (id) { return document.getElementById(id); };
    var use = el('eUse'), people = el('ePeople'), hours = el('eHours'), cur = el('eCur'), cost = el('eCost'), share = el('eShare'), live = el('eLive'), owner = el('eOwner');
    var fmt = function (n) { return Math.round(n).toLocaleString('en-IN'); };
    var money = function (n, sym) {
      if (sym === '₹') {
        if (n >= 1e7) return '₹' + (n / 1e7).toFixed(n >= 1e8 ? 0 : 1) + ' Cr';
        if (n >= 1e5) return '₹' + (n / 1e5).toFixed(n >= 1e6 ? 0 : 1) + ' L';
        return '₹' + fmt(n);
      }
      if (n >= 1e6) return sym + (n / 1e6).toFixed(1) + 'M';
      if (n >= 1e3) return sym + Math.round(n / 1e3) + 'k';
      return sym + fmt(n);
    };
    var REC = {
      assessment: ['Assessment', 'This process is small on its own. A two to four week assessment usually finds three or four similar pools of work and ranks them, so you build the one that pays back first.'],
      build: ['Fixed-scope build', 'The saving is large enough to justify a production build on this one process: an evaluation set agreed up front, guardrails, monitoring and a documented hand-over, in six to sixteen weeks.'],
      'managed-operations': ['Managed operations', 'You already run AI in production. Our managed operations retainer keeps what is live accurate and affordable, and adds this process as the next item on the improvement backlog.'],
      'fractional-caio': ['Fractional Chief AI Officer', 'The value is real but nobody senior owns it yet. A fractional AI leader two to six days a month sets the roadmap, picks vendors and sponsors the first build so it does not stall.']
    };
    var calc = function () {
      var sym = cur.options[cur.selectedIndex].getAttribute('data-sym');
      var P = +people.value, H = +hours.value, C = +cost.value || 0, S = +share.value / 100;
      el('oPeople').textContent = P; el('oHours').textContent = H; el('oShare').textContent = Math.round(S * 100) + '%';
      var weekly = P * H * S * 0.85, yearly = weekly * 46;
      el('rHours').textContent = fmt(yearly);
      el('rValue').textContent = money(yearly * C, sym);
      el('rFte').textContent = (yearly / 1800).toFixed(yearly / 1800 < 10 ? 1 : 0);
      el('rWeekly').textContent = fmt(weekly);
      var key = (P * H < 40) ? 'assessment' : live.checked ? 'managed-operations' : owner.checked ? 'fractional-caio' : 'build';
      el('rTitle').textContent = REC[key][0]; el('rWhy').textContent = REC[key][1];
      var summary = use.options[use.selectedIndex].text + ': ' + P + ' people x ' + H + ' h/week, AI share ' + Math.round(S * 100) + '%, ~' + fmt(yearly) + ' hours/year, ~' + money(yearly * C, sym) + '/year';
      el('rCta').href = '/contact/?topic=' + key + '&est=' + encodeURIComponent(summary);
    };
    use.addEventListener('change', function () { share.value = use.options[use.selectedIndex].getAttribute('data-share'); calc(); });
    cur.addEventListener('change', function () { cost.value = cur.options[cur.selectedIndex].getAttribute('data-rate'); calc(); });
    [people, hours, cost, share, live, owner].forEach(function (i) { i.addEventListener('input', calc); i.addEventListener('change', calc); });
    calc();

    var quiz = document.getElementById('quiz');
    if (quiz) {
      var answers = {};
      var STAGES = [
        [0, 'Exploring', 'You have interest but not yet the foundations. Start with an assessment: it produces the ranked use-case list, the owner and the data view that every later step depends on.', 'assessment'],
        [35, 'Ready to pilot', 'The basics are in place for one well-chosen use case. A fixed-scope build with an agreed evaluation set is the fastest way to a result you can show the board.', 'build'],
        [70, 'Ready to scale', 'You are ahead of most organisations we meet. The risk now is sprawl: pair the next build with managed operations and a governance baseline so quality and cost stay visible.', 'managed-operations']
      ];
      $$('.opts', quiz).forEach(function (o) {
        $$('button', o).forEach(function (b) {
          b.addEventListener('click', function () {
            $$('button', o).forEach(function (x) { x.classList.remove('sel'); });
            b.classList.add('sel');
            answers[o.getAttribute('data-q')] = +b.getAttribute('data-v');
            var keys = Object.keys(answers), total = $$('.opts', quiz).length;
            var score = keys.reduce(function (a, k) { return a + answers[k]; }, 0) / (total * 2) * 100;
            el('qBar').style.width = score + '%';
            el('qScore').textContent = Math.round(score) + '%';
            if (keys.length < total) {
              el('qStage').textContent = (total - keys.length) + ' question' + (total - keys.length > 1 ? 's' : '') + ' to go';
              el('qText').textContent = 'Your readiness stage appears once every question is answered.';
              return;
            }
            var st = STAGES.filter(function (s) { return score >= s[0]; }).pop();
            el('qStage').textContent = st[1] + ' (' + Math.round(score) + '%)';
            el('qText').textContent = st[2];
            var a = el('qCta'); if (a) { a.style.display = ''; a.href = '/contact/?topic=' + st[3] + '&est=' + encodeURIComponent('Readiness check: ' + Math.round(score) + '%, stage ' + st[1]); }
          });
        });
      });
    }
  }

  // ---------------------------------------------------------------- readiness checklist
  var chk = document.getElementById('chk');
  if (chk) {
    var boxes = $$('input[type=checkbox]', chk), KEY = 'my-checklist';
    var saved = {};
    try { saved = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) {}
    boxes.forEach(function (b) { if (saved[b.value]) b.checked = true; });
    var VERDICT = [
      [0, 'Early days', 'Most of the foundations are still to be laid. That is normal, and it is exactly what an assessment is for: it turns this list into a sequenced plan with owners.'],
      [40, 'Foundations forming', 'You have enough in place to run a well-scoped pilot while closing the gaps in parallel. Pick the unchecked items in Governance and Data first; they are the ones that stall projects later.'],
      [70, 'Ready to build', 'You are better prepared than most organisations we meet. The remaining items are the ones to close during a build, not before it.'],
      [90, 'Ready to scale', 'Your organisation is ready for production AI at scale. The question is now portfolio and operations: what to build next and how to keep it healthy.']
    ];
    var update = function () {
      var done = 0, state = {};
      boxes.forEach(function (b) { if (b.checked) { done++; state[b.value] = 1; } });
      try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {}
      var pct = Math.round(done / boxes.length * 100);
      $('#chkCount').textContent = done + ' / ' + boxes.length;
      $('#chkBar').style.width = pct + '%';
      $$('fieldset', chk).forEach(function (f) {
        var n = $$('input:checked', f).length, t = $$('input', f).length;
        $('legend span', f).textContent = n + ' of ' + t;
      });
      var v = VERDICT.filter(function (x) { return pct >= x[0]; }).pop();
      $('#chkStage').textContent = v[1] + ' (' + pct + '%)';
      $('#chkText').textContent = v[2];
      var a = $('#chkCta'); if (a) a.href = '/contact/?topic=assessment&est=' + encodeURIComponent('Readiness checklist: ' + done + ' of ' + boxes.length + ' items, stage ' + v[1]);
    };
    boxes.forEach(function (b) { b.addEventListener('change', update); });
    var reset = $('#chkReset'); if (reset) reset.addEventListener('click', function () { boxes.forEach(function (b) { b.checked = false; }); update(); });
    var print = $('#chkPrint'); if (print) print.addEventListener('click', function () { window.print(); });
    update();
  }

  // ---------------------------------------------------------------- share buttons on insights
  var shareBox = $('.share');
  if (shareBox) {
    var url = location.href.split('#')[0], title = document.title;
    $$('[data-share]', shareBox).forEach(function (b) {
      var kind = b.getAttribute('data-share');
      if (kind === 'linkedin') b.href = 'https://www.linkedin.com/sharing/share-offsite/?url=' + encodeURIComponent(url);
      if (kind === 'whatsapp') b.href = 'https://wa.me/?text=' + encodeURIComponent(title + ' ' + url);
      if (kind === 'x') b.href = 'https://twitter.com/intent/tweet?url=' + encodeURIComponent(url) + '&text=' + encodeURIComponent(title);
      if (kind === 'copy') b.addEventListener('click', function () {
        var done = function () {
          var t = document.createElement('div'); t.className = 'toast'; t.textContent = 'Link copied';
          document.body.appendChild(t); setTimeout(function () { t.remove(); }, 1800);
        };
        if (navigator.clipboard) navigator.clipboard.writeText(url).then(done, done); else done();
      });
    });
  }

  // ---------------------------------------------------------------- site assistant (needs CFG.assistant = deployed worker URL)
  if (CFG.assistant) {
    var box = getFloat();
    var ab = document.createElement('button');
    ab.className = 'ai-btn'; ab.type = 'button'; ab.setAttribute('aria-expanded', 'false');
    ab.innerHTML = '<i aria-hidden="true"></i><span>Ask MindYards</span>';
    box.appendChild(ab);
    var panel = document.createElement('div');
    panel.className = 'ai-panel'; panel.setAttribute('role', 'dialog'); panel.setAttribute('aria-label', 'MindYards assistant');
    panel.innerHTML =
      '<div class="ai-hd"><div>MindYards assistant<small>Answers about our services, in seconds</small></div><button type="button" aria-label="Close">×</button></div>' +
      '<div class="ai-log"></div>' +
      '<div class="ai-sug"><button type="button">What do you do?</button><button type="button">How does a fixed-scope build work?</button><button type="button">Can you help with EU AI Act compliance?</button></div>' +
      '<form class="ai-in"><input type="text" placeholder="Ask about our services…" autocomplete="off" maxlength="500"><button type="submit">Send</button></form>' +
      '<div class="ai-ft">AI-generated answers can be wrong. For anything binding, talk to us.</div>';
    document.body.appendChild(panel);
    var log = $('.ai-log', panel), input = $('input', panel), history = [];
    var add = function (role, text) {
      var m = document.createElement('div'); m.className = 'ai-m ' + role;
      if (role === 'a') {
        m.innerHTML = esc(text)
          .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+|\/[^\s)]*)\)/g, '<a href="$2">$1</a>')
          .replace(/(^|\s)(\/(?:services|industries|solutions|engagement|insights|about|contact|estimate|resources)\/[\w\-\/]*)/g, '$1<a href="$2">$2</a>');
      } else m.textContent = text;
      log.appendChild(m); log.scrollTop = log.scrollHeight; return m;
    };
    add('a', 'Hello. Ask me anything about what MindYards does, how an engagement works or whether we can help with a specific problem.');
    var send = function (text) {
      text = (text || '').trim(); if (!text) return;
      add('u', text); history.push({ role: 'user', content: text });
      $('.ai-sug', panel).style.display = 'none';
      var wait = add('a', 'Thinking'); wait.classList.add('t');
      var ctrl = new AbortController(), t = setTimeout(function () { ctrl.abort(); }, 40000);
      fetch(CFG.assistant, { method: 'POST', headers: { 'Content-Type': 'application/json' }, signal: ctrl.signal,
        body: JSON.stringify({ messages: history.slice(-12), page: location.pathname }) })
        .then(function (r) { return r.json(); })
        .then(function (j) {
          clearTimeout(t); wait.remove();
          var reply = (j && j.reply) || 'Sorry, I could not answer that. Please email contact@mindyards.in.';
          add('a', reply); history.push({ role: 'assistant', content: reply });
        })
        .catch(function () { clearTimeout(t); wait.remove(); add('a', 'The assistant is not reachable right now. Please email contact@mindyards.in.'); });
    };
    ab.addEventListener('click', function () {
      var open = panel.classList.toggle('open'); ab.setAttribute('aria-expanded', open);
      if (open) input.focus();
    });
    $('.ai-hd button', panel).addEventListener('click', function () { panel.classList.remove('open'); ab.setAttribute('aria-expanded', 'false'); });
    $$('.ai-sug button', panel).forEach(function (b) { b.addEventListener('click', function () { send(b.textContent); }); });
    $('form', panel).addEventListener('submit', function (e) { e.preventDefault(); send(input.value); input.value = ''; });
  }
})();
