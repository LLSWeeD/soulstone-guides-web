// Soulstone Guides: язык, тема, фильтры главной, вкладки билдов. Без зависимостей.
(function () {
  var root = document.documentElement;

  function save(key, value) {
    try { localStorage.setItem(key, value); } catch (_) { /* приватный режим: просто не запоминаем */ }
  }

  document.addEventListener('click', function (ev) {
    var btn = ev.target.closest('[data-act]');
    if (btn) {
      if (btn.dataset.act === 'lang') {
        var lang = root.dataset.lang === 'en' ? 'ru' : 'en';
        root.dataset.lang = lang;
        root.lang = lang;
        save('lang', lang);
      } else if (btn.dataset.act === 'theme') {
        var theme = root.dataset.theme === 'light' ? 'dark' : 'light';
        root.dataset.theme = theme;
        save('theme', theme);
      }
      return;
    }
    var tab = ev.target.closest('.tab');
    if (tab) {
      var list = tab.parentElement;
      list.querySelectorAll('.tab').forEach(function (t) {
        var on = t === tab;
        t.classList.toggle('on', on);
        t.setAttribute('aria-selected', on);
        var panel = document.getElementById(t.dataset.tab);
        if (panel) panel.hidden = !on;
      });
    }
  });

  // фильтры справочника
  var rgrid = document.getElementById('rgrid');
  if (rgrid) {
    var rq = document.getElementById('rq');
    var rcount = document.getElementById('rcount');
    var rempty = document.getElementById('empty');
    var tag = '';
    var items = Array.prototype.slice.call(rgrid.querySelectorAll('.ritem'));
    var rapply = function () {
      var text = (rq.value || '').trim().toLowerCase();
      var shown = 0;
      items.forEach(function (it) {
        var ok = (!tag || it.dataset.tags.split('|').indexOf(tag) !== -1) &&
                 (!text || it.dataset.search.indexOf(text) !== -1);
        it.hidden = !ok;
        if (ok) shown++;
      });
      rcount.textContent = shown + ' / ' + items.length;
      rempty.hidden = shown !== 0;
    };
    rq.addEventListener('input', rapply);
    document.querySelectorAll('.rbtn').forEach(function (b) {
      b.addEventListener('click', function () {
        document.querySelectorAll('.rbtn').forEach(function (x) { x.classList.toggle('on', x === b); });
        tag = b.dataset.tag;
        rapply();
      });
    });
    // при переходе по ссылке #id элемент мог быть скрыт фильтром: сбрасываем фильтры
    if (location.hash) { rq.value = ''; }
    rapply();
  }

  // фильтры главной
  var grid = document.getElementById('grid');
  if (!grid) return;
  var q = document.getElementById('q');
  var empty = document.getElementById('empty');
  var cls = '';

  function apply() {
    var text = (q.value || '').trim().toLowerCase();
    var shown = 0;
    grid.querySelectorAll('.tile').forEach(function (t) {
      var okClass = !cls || t.dataset.class.split('|').indexOf(cls) !== -1;
      var okText = !text || t.dataset.search.indexOf(text) !== -1;
      t.hidden = !(okClass && okText);
      if (!t.hidden) shown++;
    });
    empty.hidden = shown !== 0;
  }

  q.addEventListener('input', apply);
  document.querySelectorAll('.fbtn').forEach(function (b) {
    b.addEventListener('click', function () {
      document.querySelectorAll('.fbtn').forEach(function (x) { x.classList.toggle('on', x === b); });
      cls = b.dataset.class;
      apply();
    });
  });
})();
