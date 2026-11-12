(function () {
  // ---------- تب‌ها و فیلتر قیمت در صفحه شهر ----------
  var tabs = document.querySelectorAll('.tab');
  var level = '0';
  function applyFilter() {
    document.querySelectorAll('.group').forEach(function (g) {
      g.hidden = level !== '0' && g.dataset.level !== level;
    });
  }
  tabs.forEach(function (t) {
    t.addEventListener('click', function () {
      tabs.forEach(function (x) { x.classList.toggle('active', x === t); });
      document.getElementById('pane-places').hidden = t.dataset.target !== 'places';
      document.getElementById('pane-food').hidden = t.dataset.target !== 'food';
    });
  });
  document.querySelectorAll('.filters .chip').forEach(function (c) {
    c.addEventListener('click', function () {
      document.querySelectorAll('.filters .chip').forEach(function (x) { x.classList.toggle('active', x === c); });
      level = c.dataset.level;
      applyFilter();
    });
  });

  // ---------- دستیار هوشمند ----------
  var fab = document.getElementById('as-fab');
  var panel = document.getElementById('as-panel');
  if (!fab || !panel) return;
  var log = document.getElementById('as-log');
  var chips = document.getElementById('as-chips');
  var sel = document.getElementById('as-city');
  var city = panel.dataset.city || '';

  function add(cls, text) {
    var d = document.createElement('div');
    d.className = 'msg ' + cls;
    d.textContent = text;
    log.appendChild(d);
    log.scrollTop = log.scrollHeight;
  }

  function loadQuestions() {
    fetch('/api/assistant/questions?city=' + encodeURIComponent(city))
      .then(function (r) { return r.json(); })
      .then(function (d) {
        chips.innerHTML = '';
        d.questions.forEach(function (q) {
          var b = document.createElement('button');
          b.type = 'button';
          b.className = 'chip';
          b.textContent = q.q;
          b.addEventListener('click', function () { ask(q); });
          chips.appendChild(b);
        });
      });
  }

  function ask(q) {
    add('user', q.q);
    fetch('/api/assistant', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ city: city, qid: q.id })
    }).then(function (r) { return r.json(); })
      .then(function (d) { add('bot', d.answer); })
      .catch(function () { add('bot', 'خطا در دریافت پاسخ. دوباره تلاش کنید.'); });
  }

  fab.addEventListener('click', function () {
    panel.hidden = !panel.hidden;
    if (!panel.hidden && !chips.children.length) loadQuestions();
  });
  document.getElementById('as-close').addEventListener('click', function () { panel.hidden = true; });
  if (sel) sel.addEventListener('change', function () { city = sel.value; loadQuestions(); });
})();

// Hero background video: always silent; retry muted playback where autoplay is restricted.
document.addEventListener('DOMContentLoaded', function () {
  const bgVideo = document.querySelector('.hero-video');
  if (!bgVideo) return;
  bgVideo.muted = true;
  bgVideo.defaultMuted = true;
  bgVideo.volume = 0;
  const playPromise = bgVideo.play();
  if (playPromise && typeof playPromise.catch === 'function') {
    playPromise.catch(function () {
      // Some browsers block autoplay until the user interacts with the page.
    });
  }
});
