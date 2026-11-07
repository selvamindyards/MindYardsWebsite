(function () {
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
    Array.prototype.forEach.call(nav.querySelectorAll('a'), function (a) {
      var href = a.getAttribute('href') || '';
      if (href.charAt(0) !== '/') return;
      var p = href.split('#')[0].split('?')[0];
      if (!p || p === '/') return;
      if (path === p) a.classList.add('on');
      else if (a.parentNode.classList.contains('dd') && path.indexOf(p) === 0) a.classList.add('on');
    });
  }

  // Contact page: preselect the topic the visitor came from and compose a readable mailto.
  var form = document.getElementById('contactForm');
  if (form) {
    var topic = null;
    try { topic = new URLSearchParams(location.search).get('topic'); } catch (e) {}
    var topics = window.MY_TOPICS || {};
    var sel = document.getElementById('service');
    var from = topic && topics[topic] ? topics[topic] : null;
    if (from && sel) {
      Array.prototype.forEach.call(sel.options, function (o) { if (o.text === from[0]) sel.value = o.value || o.text; });
    }
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var v = function (id) { return (document.getElementById(id).value || '').trim(); };
      var service = v('service') || 'Not sure yet';
      var subject = 'MindYards enquiry: ' + (from ? from[1] : service) + (v('company') ? ' (' + v('company') + ')' : '');
      var body = 'Name: ' + v('name') + '\n' +
                 'Email: ' + v('email') + '\n' +
                 'Company: ' + (v('company') || '-') + '\n' +
                 'Interested in: ' + service + '\n' +
                 (from ? 'Regarding: ' + from[1] + '\n' : '') + '\n' +
                 v('msg') + '\n';
      window.location.href = 'mailto:contact@mindyards.in?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
    });
  }
})();
