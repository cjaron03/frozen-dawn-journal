/* ================= what every chapter shares =================
   the chapter pages grew the same machinery one copy at a time: the typed
   title and its intro, the tabbed deck, the cards that rise as they scroll
   in, the numbers that count up, the read marker and the reading layer
   switch. the one copy lives here now. each page keeps its own instruments
   and calls in for the rest at the point in its own script where its copy
   used to run, so nothing starts in a different order than it did. */
(function(){
  var RM = !!(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches);
  function arr(n, root){ return [].slice.call((root || document).querySelectorAll(n)); }

  /* a one shot animation class comes off once it has played, and so does
     the delay it was staggered with */
  function clearOn(el, cls){
    function h(e){
      if (e.target !== el) return;
      el.classList.remove(cls);
      el.style.animationDelay = '';
      el.removeEventListener('animationend', h);
      el.removeEventListener('animationcancel', h);
    }
    el.addEventListener('animationend', h);
    el.addEventListener('animationcancel', h);
  }

  function countUp(el){
    if (RM || el.dataset.counted) return;
    var m = el.textContent.trim().match(/^([\d,]+)(.*)$/);
    if (!m) return;
    var target = parseInt(m[1].replace(/,/g, ''), 10), suf = m[2];
    if (!(target > 0)) return;
    el.dataset.counted = '1';
    var t0 = 0;
    el.textContent = '0' + suf;
    requestAnimationFrame(function run(t){
      if (!t0) t0 = t;
      var k = Math.min((t - t0) / 900, 1), e = 1 - Math.pow(1 - k, 3);
      el.textContent = Math.round(target * e).toLocaleString('en-US') + suf;
      if (k < 1) requestAnimationFrame(run);
    });
  }

  /* ================= the intro =================
     the title types itself in, the rest of the page rises under it, and the
     frame is marked done when that lands. o.done is how long to wait before
     marking it done anyway, o.pad is the slack on the typed width, and
     o.still marks it done at once under reduced motion. the Architect and
     Maeve open differently and keep their own. */
  function intro(o){
    o = o || {};
    var frame = document.getElementById('apFrame');
    if (!frame) return;
    var doc   = frame.querySelector('.ap-doc');
    var title = frame.querySelector('.ap-title');
    var pad   = o.pad || 2;

    function measureTitle(){
      var cs = getComputedStyle(title);
      var probe = document.createElement('span');
      probe.style.cssText = 'position:absolute;visibility:hidden;white-space:nowrap;font:'
        + cs.font + ';letter-spacing:' + cs.letterSpacing + ';text-transform:' + cs.textTransform;
      probe.textContent = title.textContent;
      document.body.appendChild(probe);
      title.style.setProperty('--tw', (probe.offsetWidth + pad) + 'px');
      probe.remove();
    }
    measureTitle();
    if (o.still && RM) frame.classList.add('done');
    title.addEventListener('animationend', function(e){
      if (e.animationName === 'apType'){ title.style.width = 'auto'; title.style.overflow = 'visible'; }
    });
    frame.addEventListener('animationend', function(e){
      if (e.animationName === 'apUp') frame.classList.add('done');
    });
    setTimeout(function(){ frame.classList.add('done'); }, o.done || 3200);

    /* any real scroll intent lands the intro immediately. wheel and touch go on
       the frame, not the doc: during the intro the black overlay sits on top,
       so events never reach the scroll body. */
    function skipIntro(){
      if (!frame.classList.contains('done')) frame.classList.add('done');
    }
    frame.addEventListener('wheel',     skipIntro, { passive:true });
    frame.addEventListener('touchmove', skipIntro, { passive:true });
    doc.addEventListener('scroll', function(){ if (doc.scrollTop > 0) skipIntro(); }, { passive:true });
    window.addEventListener('keydown', function(e){
      if (/^(ArrowDown|ArrowUp|PageDown|PageUp|Home|End|Spacebar| )$/.test(e.key)) skipIntro();
    }, { passive:true });
    window.addEventListener('resize', function(){ measureTitle(); });
    var replay = document.getElementById('apReplay');
    if (replay) replay.onclick = function(){
      title.style.width = ''; title.style.overflow = ''; measureTitle();
      frame.classList.remove('done');
      frame.classList.remove('play'); void frame.offsetWidth; frame.classList.add('play');
      doc.scrollTop = 0;
    };
  }

  /* ================= the deck and the cards =================
     o.grids   what staggers in when its block or pane arrives
     o.wait    how long to wait on the intro before the cards arm anyway,
               with a mutation observer and without one
     o.pane    runs each time a pane opens
     o.settled runs once the stage has finished changing height
     o.arrive  runs when a block arrives, next to the count up */
  function cards(o){
    o = o || {};
    var frame = document.getElementById('apFrame');
    var doc   = document.querySelector('.ap-doc');
    if (!doc) return;
    var GRIDS = o.grids || [];
    var wait  = o.wait || [4000, 3000];

    function stagger(root){
      if (RM) return;
      GRIDS.forEach(function(sel){
        arr(sel, root).forEach(function(el, n){
          if (n > 15) return;
          el.style.animationDelay = (n * 0.045) + 's';
          el.classList.remove('ap-pop'); void el.offsetWidth; el.classList.add('ap-pop');
          clearOn(el, 'ap-pop');
        });
      });
    }
    function settle(root){
      arr('.ap-pop', root).forEach(function(el){
        el.classList.remove('ap-pop'); el.style.animationDelay = '';
      });
      if (root.classList.contains('ap-pop')){
        root.classList.remove('ap-pop'); root.style.animationDelay = '';
      }
    }

    /* ---------------- the deck ---------------- */
    var deck = document.getElementById('apDeck');
    if (deck){
      var panes  = arr('.ap-pane', deck);
      var strips = arr('.ap-dstrip', deck);
      var stage  = deck.querySelector('.ap-dstage');
      var bPrev  = deck.querySelector('.ap-dstep.prev');
      var bNext  = deck.querySelector('.ap-dstep.next');
      var cur = 0, morphT = 0;

      function tabs(s){ return s.querySelectorAll('.ap-dtab'); }

      /* a full row of tabs will not fit a phone at full length, so swap in the
         short labels below 640px and put them back when there is room again.
         a deck with no short labels is left as it is. */
      var NARROW = window.matchMedia('(max-width:640px)');
      strips.forEach(function(s){
        tabs(s).forEach(function(b){
          var n = b.lastChild;
          if (n && n.nodeType === 3) b.setAttribute('data-long', n.nodeValue);
        });
      });
      function fitTabs(){
        var short = NARROW.matches;
        strips.forEach(function(s){
          tabs(s).forEach(function(b){
            var n = b.lastChild; if (!n || n.nodeType !== 3) return;
            var want = short ? (b.getAttribute('data-short') || b.getAttribute('data-long'))
                             : b.getAttribute('data-long');
            if (want && n.nodeValue !== want) n.nodeValue = want;
          });
        });
      }

      function ink(){
        strips.forEach(function(s){
          var bar = s.querySelector('.ap-dink'), t = tabs(s)[cur];
          if (!bar || !t) return;
          bar.style.width = t.offsetWidth + 'px';
          bar.style.transform = 'translate3d(' + t.offsetLeft + 'px,0,0)';
        });
      }
      function centre(){
        strips.forEach(function(s){
          var t = tabs(s)[cur]; if (!t) return;
          var want = t.offsetLeft - (s.clientWidth - t.offsetWidth) / 2;
          want = Math.max(0, Math.min(want, s.scrollWidth - s.clientWidth));
          if (s.scrollTo) s.scrollTo({ left: want, behavior: RM ? 'auto' : 'smooth' });
          else s.scrollLeft = want;
        });
      }
      function fullName(i){
        var t = tabs(strips[0])[i];
        return t ? (t.getAttribute('data-full') || t.textContent.trim()) : '';
      }
      function step(btn, i, kicker){
        if (!btn) return;
        if (i < 0 || i >= panes.length){ btn.disabled = true; btn.innerHTML = ''; return; }
        btn.disabled = false;
        btn.innerHTML = '<em>' + kicker + '</em><b>' + fullName(i) + '</b>';
      }
      function deckTop(){
        var a = deck.getBoundingClientRect(), b = doc.getBoundingClientRect();
        return doc.scrollTop + (a.top - b.top);
      }

      function go(i, snap){
        i = Math.max(0, Math.min(panes.length - 1, i));
        if (i === cur) return;
        var back = i < cur;
        var from = stage.offsetHeight;
        settle(panes[cur]);
        panes[cur].classList.remove('on', 'enter', 'rev');
        cur = i;
        panes[cur].classList.add('on');
        strips.forEach(function(s){
          var ts = tabs(s);
          for (var n = 0; n < ts.length; n++){
            ts[n].classList.toggle('on', n === cur);
            ts[n].setAttribute('aria-selected', n === cur ? 'true' : 'false');
            ts[n].setAttribute('tabindex', n === cur ? '0' : '-1');
          }
        });
        ink(); centre();
        step(bPrev, cur - 1, 'Back to');
        step(bNext, cur + 1, 'Next');
        stagger(panes[cur]);
        arr('.ap-figs b', panes[cur]).forEach(countUp);
        if (o.pane) o.pane(panes[cur]);
        if (!RM){
          panes[cur].classList.add('enter');
          if (back) panes[cur].classList.add('rev');
          clearOn(panes[cur], 'enter');
          clearOn(panes[cur], 'rev');
        }
        var to = stage.offsetHeight;
        if (!RM && from && to && from !== to){
          clearTimeout(morphT);
          stage.classList.remove('morph');
          stage.style.height = from + 'px';
          void stage.offsetHeight;
          stage.classList.add('morph');
          stage.style.height = to + 'px';
          morphT = setTimeout(function(){
            stage.classList.remove('morph');
            stage.style.height = '';
            if (o.settled) o.settled();
          }, 470);
        }
        if (snap){
          var want = Math.max(0, deckTop() - 6);
          if (doc.scrollTo) doc.scrollTo({ top: want, behavior: RM ? 'auto' : 'smooth' });
          else doc.scrollTop = want;
        }
      }

      strips.forEach(function(s){
        s.addEventListener('click', function(e){
          var t = e.target.closest ? e.target.closest('.ap-dtab') : null;
          if (!t) return;
          go(+t.getAttribute('data-i'), false);
        });
        s.addEventListener('keydown', function(e){
          if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
          e.preventDefault();
          go(cur + (e.key === 'ArrowRight' ? 1 : -1), false);
          var t = tabs(s)[cur]; if (t) t.focus();
        });
      });
      if (bPrev) bPrev.addEventListener('click', function(){ go(cur - 1, true); });
      if (bNext) bNext.addEventListener('click', function(){ go(cur + 1, true); });
      step(bPrev, -1, 'Back to');
      step(bNext, 1, 'Next');
      fitTabs();
      requestAnimationFrame(function(){ ink(); });
      window.addEventListener('resize', function(){ fitTabs(); ink(); });
      if (NARROW.addEventListener) NARROW.addEventListener('change', function(){ fitTabs(); ink(); });
      else if (NARROW.addListener) NARROW.addListener(function(){ fitTabs(); ink(); });
    }

    /* ---------------- count up + scroll reveal ---------------- */
    var rest = document.querySelector('.ap-rest');
    var pub = [];
    if (rest){
      for (var n = 0; n < rest.children.length; n++){
        var k = rest.children[n];
        if (k === deck) break;
        pub.push(k);
      }
    }
    if (deck) pub.push(deck);

    /* what a block does on arrival, short of the rise itself */
    function greet(el){
      if (el.classList.contains('ap-stats')) arr('b', el).forEach(countUp);
      if (el === deck) arr('.ap-pane.on .ap-figs b', el).forEach(countUp);
      if (o.arrive) o.arrive(el);
    }
    function land(el){
      if (el.classList.contains('ap-rv')){
        el.classList.add('in');
        el.addEventListener('animationend', function h(){
          el.classList.remove('in'); el.classList.add('set');
          el.removeEventListener('animationend', h);
        });
      }
      greet(el);
      stagger(el);
    }
    function revealAll(){ pub.forEach(function(el){ el.classList.remove('ap-rv'); el.classList.add('set'); }); }
    function onScreen(el, lim){
      return el.getClientRects().length > 0 && el.getBoundingClientRect().top < lim;
    }
    /* the first screen fades in with the intro, so its numbers start counting
       as the fade starts, and are already moving the moment they can be seen. */
    if (frame) frame.addEventListener('animationstart', function(e){
      if (e.animationName !== 'apUp' || e.target !== rest) return;
      var lim = doc.getBoundingClientRect().bottom;
      pub.forEach(function(el){ if (onScreen(el, lim)) greet(el); });
    });

    var armed = false;
    function arm(){
      if (armed) return;
      armed = true;
      if (RM || !window.IntersectionObserver){ revealAll(); return; }
      /* whatever is already on screen came in with the intro's fade. hiding it
         here only to rise it again made the first screen load twice, so it is
         set as it stands, and only what is still below the fold waits. */
      var lim = doc.getBoundingClientRect().bottom;
      var later = pub.filter(function(el){
        if (!onScreen(el, lim)) return true;
        if (el !== deck) el.classList.add('set');
        greet(el);
        return false;
      });
      later.forEach(function(el){ if (el !== deck) el.classList.add('ap-rv'); });
      var io = new IntersectionObserver(function(es){
        es.forEach(function(e){
          if (!e.isIntersecting) return;
          io.unobserve(e.target);
          land(e.target);
        });
      }, { root: doc, rootMargin: '0px 0px -8% 0px', threshold: 0.01 });
      later.forEach(function(el){ io.observe(el); });

      /* a jump scroll (end key, a restored position) can carry an element from
         below the fold to above it without ever intersecting, and the observer
         reports nothing for something it has never seen. sweep for those and
         set them outright: they are already behind the reader. */
      function setNow(el){
        io.unobserve(el);
        el.classList.remove('ap-rv'); el.classList.add('set');
        settle(el);
        greet(el);
      }
      var sweeping = false;
      function sweep(){
        sweeping = false;
        var top = doc.getBoundingClientRect().top, left = 0;
        pub.forEach(function(el){
          var c = el.classList;
          if (!c.contains('ap-rv') || c.contains('in') || c.contains('set')) return;
          if (el.getBoundingClientRect().bottom < top) setNow(el); else left += 1;
        });
        if (!left) doc.removeEventListener('scroll', onScroll);
      }
      function onScroll(){
        if (sweeping) return;
        sweeping = true;
        requestAnimationFrame(sweep);
      }
      doc.addEventListener('scroll', onScroll, { passive: true });
    }
    if (!frame || frame.classList.contains('done')) arm();
    else if (window.MutationObserver){
      var mo = new MutationObserver(function(){
        if (frame.classList.contains('done')){ mo.disconnect(); arm(); }
      });
      mo.observe(frame, { attributes: true, attributeFilter: ['class'] });
      setTimeout(function(){ if (!armed){ mo.disconnect(); arm(); } }, wait[0]);
    } else setTimeout(arm, wait[1]);
  }

  /* ================= how far the reader actually got =================
     a chapter counts when its body has been scrolled to the bottom, not when
     the page was opened. N is the chapter's bit in fd.read. */
  function progress(N){
    var doc = document.querySelector('.ap-doc');
    if (!doc) return;
    function mark(){
      var s, was;
      try {
        s = window.localStorage;
        was = parseInt(s.getItem('fd.read'), 10) || 0;
        var v = was | (1 << N);
        s.setItem('fd.read', String(v));
        if (v === 254) s.setItem('fd.ok', '1');
      } catch (e) { return; }
      /* the first time each chapter is finished, and when, in the order it
         happened. only a first finish that this script actually saw goes in,
         so the log never claims more than it witnessed. Maeve's page reads it
         back. it is never sent anywhere. */
      if (was & (1 << N)) return;
      try {
        var log = JSON.parse(s.getItem('fd.log') || '[]');
        if (!Array.isArray(log)) log = [];
        log.push([N, Date.now()]);
        s.setItem('fd.log', JSON.stringify(log));
      } catch (e) {}
    }
    function check(){
      if (doc.scrollHeight - doc.clientHeight < 200) return;
      if (doc.scrollTop + doc.clientHeight >= doc.scrollHeight - 80) mark();
    }
    doc.addEventListener('scroll', check, { passive: true });
  }

  /* ================= the reading layer switch =================
     the same control and the same storage key on every chapter, so whichever
     side the reader picked follows them from page to page. the default is
     baked into the markup, so a page is correct before this runs at all. */
  function layers(){
    var KEY = 'fd-layer';
    var seg = document.querySelector('.rl-seg');
    if (!seg) return;
    var btns = [].slice.call(seg.querySelectorAll('button'));

    /* a pane can lose everything it had to the build layer. a tab that opens
       onto nothing reads as broken, so the pane says what is behind the switch
       instead of showing an empty box. a pane may name its own wording. */
    function stubs(){
      [].slice.call(document.querySelectorAll('.ap-pane')).forEach(function(pane){
        var stub = pane.querySelector('.rl-stub');
        var real = [].slice.call(pane.children).some(function(el){
          return el !== stub && getComputedStyle(el).display !== 'none';
        });
        if (real){ if (stub) stub.hidden = true; return; }
        if (!stub){
          stub = document.createElement('p');
          stub.className = 'rl-stub';
          stub.textContent = pane.getAttribute('data-stub')
                           || 'This section is all workings. '
                            + 'Switch to How I built it to read it.';
          pane.appendChild(stub);
        }
        stub.hidden = false;
      });
    }

    /* the scroll reveal observer watches a block that is hidden behind the
       switch, but a hidden block has no box, so it never intersects and it is
       never landed. once the switch shows it, one that is still below the fold
       intersects on the next scroll and rises normally. one that is already at
       or above the fold is behind the reader and will never intersect again,
       so it arrives from behind the switch still at opacity zero. set those
       outright. */
    function rescue(){
      var sc = document.querySelector('.ap-doc');
      if (!sc) return;
      var lim = sc.getBoundingClientRect().bottom;
      [].slice.call(document.querySelectorAll('.ap-rv')).forEach(function(el){
        if (getComputedStyle(el).display === 'none') return;
        if (el.classList.contains('in') || el.classList.contains('set')) return;
        if (el.getBoundingClientRect().top > lim) return;
        el.classList.remove('ap-rv');
        el.classList.add('set');
      });
    }

    function apply(layer, save){
      document.body.classList.toggle('build', layer === 'build');
      btns.forEach(function(b){
        var on = b.getAttribute('data-layer') === layer;
        b.classList.toggle('on', on);
        b.setAttribute('aria-pressed', on ? 'true' : 'false');
      });
      stubs();
      rescue();
      if (save){ try { localStorage.setItem(KEY, layer); } catch (e) {} }
    }

    btns.forEach(function(b){
      b.addEventListener('click', function(){
        apply(b.getAttribute('data-layer'), true);
      });
    });

    var saved = null;
    try { saved = localStorage.getItem(KEY); } catch (e) {}
    apply(saved === 'build' ? 'build' : 'story', false);
  }

  window.Chapter = { intro: intro, cards: cards, progress: progress, layers: layers };
})();
