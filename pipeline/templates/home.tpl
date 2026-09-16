<h2>The homepage</h2>
<p class="subtitle">__SUBTITLE__</p>

<style>
.tl { --mono: ui-monospace,"SF Mono",Menlo,monospace; --ice:#7dd3fc; --amb:#ffb454; }
.tl-frame { position:relative; background:#0f1216; border:1px solid #1d232a; border-radius:10px; overflow:hidden; }

/* ---- snow ---- */
.tl-snow { position:absolute; inset:0; overflow:hidden; pointer-events:none; z-index:1; }
.tl-snow span { position:absolute; top:-8px; border-radius:50%; background:#dbe9f5; animation-name:tlfall; animation-timing-function:linear; animation-iteration-count:infinite; }
@keyframes tlfall { from { transform:translate3d(0,-10px,0) } to { transform:translate3d(var(--dx),460px,0) } }

/* ---- header ---- */
.tl-head { position:relative; z-index:3; display:flex; align-items:baseline; gap:10px; padding:16px 22px 0; }
.tl-head b { color:#f2f6f8; font-size:15px; font-weight:700; letter-spacing:-.015em; }
.tl-head i { color:#7c8891; font-size:11px; font-style:normal; letter-spacing:.06em; }
.tl-head nav { margin-left:auto; display:flex; gap:16px; font-size:11px; color:#6c7782; }
.tl-meta { position:relative; z-index:3; padding:2px 22px 0; font-family:var(--mono); font-size:9.5px; letter-spacing:.15em; text-transform:uppercase; color:#4e5a66; }

/* ---- stage ---- */
.tl-stage { position:relative; z-index:2; height:238px; margin:10px 22px 0; }
.tl-stage svg { position:absolute; inset:0; width:100%; height:100%; overflow:visible; }
.tl-grain { fill:#22506d; opacity:0; animation:tlgrain 1.1s ease __GRAINAT__s forwards; }
@keyframes tlgrain { to { opacity:.3 } }
.tl-trace { fill:none; stroke:#2c688a; stroke-width:2; stroke-linejoin:round; stroke-dasharray:__LEN__; stroke-dashoffset:__LEN__; animation:tldraw 3.6s cubic-bezier(.32,.02,.2,1) forwards; }
.tl-glow { fill:none; stroke:#7dd3fc; stroke-width:5; opacity:.13; filter:blur(3px); stroke-dasharray:__LEN__; stroke-dashoffset:__LEN__; animation:tldraw 3.6s cubic-bezier(.32,.02,.2,1) forwards; }
@keyframes tldraw { to { stroke-dashoffset:0 } }

/* ---- dots ---- */
.tl-d { position:absolute; width:26px; height:26px; margin:-13px 0 0 -13px; display:grid; place-items:center; cursor:pointer; opacity:0; transform:scale(.2); animation:tlpop .5s cubic-bezier(.2,1.5,.4,1) forwards; text-decoration:none; }
@keyframes tlpop { to { opacity:1; transform:scale(1) } }
.tl-d i { width:7px; height:7px; border-radius:50%; background:#7dd3fc; transition:transform .18s, box-shadow .18s; }
.tl-d.major i { width:10px; height:10px; box-shadow:0 0 0 3px #0f1216, 0 0 0 4px #7dd3fc4d; }
.tl-d.arch2 i { width:10px; height:10px; box-shadow:0 0 0 3px #0f1216, 0 0 0 4px #7dd3fc4d; }
.tl-d.arch i { width:12px; height:12px; background:#ffb454; box-shadow:0 0 0 3px #0f1216, 0 0 0 5px #ffb4543d, 0 0 16px #ffb45480; }
.tl-d:hover i { transform:scale(1.45); }
.tl-d:hover { z-index:20; }
.tl-d.arch:after { content:""; position:absolute; top:50%; left:50%; width:12px; height:12px; margin:-6px 0 0 -6px; border-radius:50%; border:1px solid #ffb454; opacity:0; animation:tlring 3.6s ease-out 4.1s infinite; pointer-events:none; }
@keyframes tlring { 0% { transform:scale(1); opacity:.5 } 60% { transform:scale(3); opacity:0 } 100% { transform:scale(3); opacity:0 } }

/* ---- hover card ---- */
.tl-card { position:absolute; left:50%; transform:translate(-50%,4px); width:212px; background:#151b22; border:1px solid #26303b; border-radius:7px; padding:9px 11px 10px; opacity:0; pointer-events:none; transition:opacity .16s, transform .16s; }
.tl-card.above { bottom:22px; }
.tl-card.below { top:22px; }
.tl-d:hover .tl-card { opacity:1; transform:translate(-50%,0); }
.tl-card.edgeL { left:-13px; transform:translate(0,4px); }
.tl-card.edgeR { left:auto; right:-13px; transform:translate(0,4px); }
.tl-d:hover .tl-card.edgeL, .tl-d:hover .tl-card.edgeR { transform:translate(0,0); }
.tl-card em { display:block; font-family:var(--mono); font-size:9px; letter-spacing:.14em; text-transform:uppercase; color:#7c8891; font-style:normal; }
.tl-card b { display:block; font-size:13px; font-weight:600; color:#f2f6f8; letter-spacing:-.01em; margin:3px 0 6px; }
.tl-card code { display:block; font-family:var(--mono); font-size:9.5px; line-height:1.5; color:#7e8a96; border-top:1px solid #212831; padding-top:6px; }
.tl-d.arch .tl-card { border-color:#3a3020; }
.tl-d.arch .tl-card b { color:#ffb454; }

/* ---- silence bracket ---- */
.tl-sil { position:absolute; left:39.27%; width:32.98%; bottom:4px; text-align:center; opacity:0; animation:tlfade .8s ease 2.05s forwards; }
.tl-sil div { height:5px; border:1px solid #2a3440; border-top:none; border-radius:0 0 3px 3px; }
.tl-sil span { display:block; margin-top:5px; font-family:var(--mono); font-size:9.5px; letter-spacing:.14em; text-transform:uppercase; color:#54626e; }
@keyframes tlfade { to { opacity:1 } }

/* ---- chapter bands ---- */
.tl-bands { position:relative; z-index:2; display:flex; margin:0 22px; padding-top:9px; border-top:1px solid #1b212a; gap:1px; }
.tl-bands div { padding:7px 0 16px; font-size:10.5px; color:#77828c; position:relative; opacity:0; animation:tlfade .6s ease forwards; }
.tl-bands div:before { content:""; position:absolute; top:-1px; left:0; right:1px; height:1px; background:#2c688a; }
.tl-bands div.q:before { background:#1e2932; }
.tl-bands div.p:before { background:#7dd3fc; }
.tl-bands b { color:#aeb8c0; font-weight:500; }

/* ---- notes + themes ---- */

.tl-th { margin-top:22px; display:grid; grid-template-columns:repeat(4,1fr); gap:10px; }
.tl-thc { border:1px solid #1d232a; border-radius:8px; overflow:hidden; background:#0f1216; }
.tl-thb { height:62px; position:relative; overflow:hidden; border-bottom:1px solid #1a2029; }
.tl-thb u { position:absolute; inset:0; text-decoration:none; }
.tl-thn { padding:10px 12px 12px; }
.tl-thn b { display:block; font-size:12px; color:#f2f6f8; font-weight:600; margin-bottom:4px; }
.tl-thn span { display:block; font-size:11px; line-height:1.5; color:#828d96; }

/* ---- ambient sky, one pass ---- */
.tl-sky { position:relative; aspect-ratio:1000/74; z-index:2; }
.tl-sky svg { position:absolute; inset:0; width:100%; height:100%; overflow:hidden; }

/* ---- hero ---- */
.tl-hero { position:relative; z-index:3; padding:18px 22px 4px; }
.tl-hero h1 { margin:0; font-size:26px; line-height:1.22; letter-spacing:-.022em; font-weight:650; color:#f2f6f8; max-width:20ch; }
.tl-stats { display:flex; gap:30px; margin-top:16px; }
.tl-stats div b { display:block; font-size:23px; font-weight:600; letter-spacing:-.02em; color:#7dd3fc; font-variant-numeric:tabular-nums; }
.tl-stats div span { display:block; margin-top:2px; font-family:var(--mono); font-size:9px; letter-spacing:.13em; text-transform:uppercase; color:#6a7783; }
.tl-stats div.dim b { color:#6a7783; }
.tl-cta { display:flex; gap:9px; margin-top:18px; flex-wrap:wrap; }
.tl-cta a { font-size:12.5px; padding:8px 14px; border-radius:6px; text-decoration:none; color:#c4ced6; border:1px solid #232b34; background:#141920; transition:border-color .18s, color .18s; }
.tl-cta a:hover { border-color:#33404c; color:#eef3f7; }
.tl-cta a.pri { background:#16303f; border-color:#23506b; color:#bfe6fb; }
.tl-cta a.pri:hover { border-color:#3a7ea3; color:#e4f5ff; }

/* ---- scan pulse on the finished line ---- */
.tl-scan { fill:none; stroke:#7dd3fc; stroke-width:2.5; opacity:0; stroke-linejoin:round;
  stroke-dasharray:52 __LEN__; stroke-dashoffset:52; animation:tlscan 9s linear __SCANAT__s infinite; }
@keyframes tlscan {
  0%   { opacity:0; stroke-dashoffset:52 }
  6%   { opacity:.55 }
  44%  { opacity:.55 }
  50%  { opacity:0; stroke-dashoffset:-__LEN__ }
  100% { opacity:0; stroke-dashoffset:-__LEN__ }
}

/* ---- scroll reveal, the only script on this page ---- */
.tl-rev { opacity:0; transform:translateY(14px); transition:opacity .6s cubic-bezier(.2,.8,.2,1), transform .6s cubic-bezier(.2,.8,.2,1); }
.tl-rev.in { opacity:1; transform:none; }

__COUNTERCSS__

@media (prefers-reduced-motion: reduce) {
  .tl-snow span, .tl-earth, .tl-earth *, .tl-scan { animation:none !important; }
  .tl-trace, .tl-glow { animation:none !important; stroke-dashoffset:0 !important; }
  .tl-d, .tl-bands div, .tl-sil { animation:none !important; opacity:1 !important; transform:none !important; }
  .tl-stats div b { animation:none !important; }
  .tl-rev { opacity:1; transform:none; transition:none; }
}
</style>

<div class="tl">

  <!-- ================= THE HOMEPAGE ================= -->
  <div class="tl-frame">
    <div class="tl-snow">
      __SNOW__
    </div>

    <div class="tl-sky">
      <svg viewBox="0 0 1000 74">
        <defs>
          <clipPath id="gclip"><circle cx="0" cy="0" r="9"/></clipPath>
          <radialGradient id="gshade" cx="33%" cy="29%" r="80%">
            <stop offset="0%" stop-color="#ffffff" stop-opacity=".13"/>
            <stop offset="52%" stop-color="#ffffff" stop-opacity="0"/>
            <stop offset="100%" stop-color="#000000" stop-opacity=".52"/>
          </radialGradient>
        </defs>
        <path d="__ARC__" fill="none" stroke="#1b242e" stroke-width="1"/>
        <g transform="translate(34,46)">
          <g><circle r="14" fill="#ffd257" opacity=".06"/>
            <animateTransform attributeName="transform" type="scale" dur="11.3s" repeatCount="indefinite"
              values="1;1.09;0.97;1.05;1" keyTimes="0;0.28;0.55;0.79;1" calcMode="spline"
              keySplines=".4 0 .6 1;.4 0 .6 1;.4 0 .6 1;.4 0 .6 1"/></g>
          <g><circle r="7.5" fill="#ffd257" opacity=".11"/>
            <animateTransform attributeName="transform" type="scale" dur="7.1s" repeatCount="indefinite"
              values="1;1.07;0.98;1" keyTimes="0;0.34;0.68;1" calcMode="spline"
              keySplines=".4 0 .6 1;.4 0 .6 1;.4 0 .6 1"/></g>
          <circle r="3.9" fill="#ffdc78" opacity=".92">
            <animate attributeName="opacity" dur="5.9s" repeatCount="indefinite"
              values=".92;.99;.88;.95;.92" keyTimes="0;0.22;0.49;0.74;1" calcMode="spline"
              keySplines=".4 0 .6 1;.4 0 .6 1;.4 0 .6 1;.4 0 .6 1"/>
          </circle>
        </g>
        <g class="tl-earth">
          <circle r="9" fill="#2b74a8"/>
          <g clip-path="url(#gclip)">
            <g fill="#4f9c64">
              <animate attributeName="opacity" dur="__TRAV__s" fill="freeze" values="1;1;.85;.45;.1;.05" keyTimes="0;0.3;0.45;0.62;0.85;1"/>
              <animateTransform attributeName="transform" type="translate" from="0 0" to="-18 0" dur="__SPIN__s" repeatCount="__SPINS__"/>
              <g transform="translate(-18,0)">__LAND__</g><g>__LAND__</g><g transform="translate(18,0)">__LAND__</g>
            </g>
            <ellipse cx="0" cy="-9" rx="9" fill="#eaf4fb"><animate attributeName="ry" dur="__TRAV__s" fill="freeze" values="1.1;2.2;4.6;7.2;9;9" keyTimes="0;0.3;0.5;0.7;0.88;1"/></ellipse>
            <ellipse cx="0" cy="9" rx="9" fill="#eaf4fb"><animate attributeName="ry" dur="__TRAV__s" fill="freeze" values="1.1;2.2;4.6;7.2;9;9" keyTimes="0;0.3;0.5;0.7;0.88;1"/></ellipse>
            <circle r="9" fill="#cfe2f0"><animate attributeName="opacity" dur="__TRAV__s" fill="freeze" values="0;0.05;0.3;0.68;0.92;0.95" keyTimes="0;0.3;0.5;0.7;0.88;1"/></circle>
            <circle r="9" fill="#04060b"><animate attributeName="opacity" dur="__TRAV__s" fill="freeze" values="0;0;0.1;0.42;0.7;0.78" keyTimes="0;0.5;0.68;0.82;0.94;1"/></circle>
          </g>
          <circle r="9" fill="url(#gshade)"/>
          <animateMotion dur="__TRAV__s" fill="freeze" path="__ARC__"/>
        </g>
      </svg>
    </div>

    <div class="tl-head"><b>Frozen Dawn</b><i>DEV JOURNAL</i>
      <nav><span>The Architect</span><span>Get the mod</span><span>About</span></nav>
    </div>
    <div class="tl-meta">__META__</div>

    <div class="tl-hero">
      <h1>__HEADLINE__</h1>
      <div class="tl-stats">__STATS__</div>
      <div class="tl-cta"><a class="pri" href="/architect">Meet the Architect</a><a href="/journal">Read the journal</a><a href="__REPO__">Get the mod</a></div>
    </div>

    <div class="tl-stage">
      <svg viewBox="0 0 1000 200" preserveAspectRatio="none">
        <path class="tl-grain" d="__GRAIN__"/>
        <polyline class="tl-glow" points="__POLY__"/>
        <polyline class="tl-trace" points="__POLY__"/>
        <polyline class="tl-scan" points="__POLY__"/>
      </svg>
      __DOTS__
      <div class="tl-sil" style="left:__SILX__%;width:__SILW__%"><div></div><span>__DARK__ days</span></div>
    </div>

    <div class="tl-bands">__BANDS__</div>
    </div>
  </div>

  <!-- ================= PER-PAGE THEMES ================= -->
  <div class="tl-th">
    <div class="tl-thc tl-rev">
      <div class="tl-thb" style="background:linear-gradient(160deg,#0b1016,#121a22)">
        <u style="background:repeating-linear-gradient(115deg,transparent 0 13px,#7dd3fc0f 13px 14px)"></u>
      </div>
      <div class="tl-thn"><b>The Cold</b><span>Thin diagonal frost. Widest line-height on the site. It should feel empty.</span></div>
    </div>
    <div class="tl-thc tl-rev">
      <div class="tl-thb" style="background:#0a0d11">
        <u style="background:radial-gradient(circle at 30% 55%,#ffb4541f,transparent 58%),repeating-linear-gradient(0deg,transparent 0 6px,#ffb4540a 6px 7px)"></u>
      </div>
      <div class="tl-thn"><b>The Architect</b><span>The only amber page. Scanlines, mono headers, and it watches your cursor.</span></div>
    </div>
    <div class="tl-thc tl-rev">
      <div class="tl-thb" style="background:#0f1216">
        <u style="background:linear-gradient(90deg,#7dd3fc00,#7dd3fc26 42%,#7dd3fc00 44%,#7dd3fc00)"></u>
      </div>
      <div class="tl-thn"><b>The Crunch</b><span>Dense. Tight leading, two columns, commits stacked like a wall.</span></div>
    </div>
    <div class="tl-thc tl-rev">
      <div class="tl-thb" style="background:#0c0f13"><u style="background:linear-gradient(180deg,#0c0f13,#10151b)"></u></div>
      <div class="tl-thn"><b>The Silence</b><span>No texture at all. One paragraph, centred, enormous margins. Snow stops.</span></div>
    </div>
  </div>

</div>

<script>
/* The one script on the homepage: lift each section in as it arrives. */
(function () {
  var items = document.querySelectorAll('.tl-rev');
  if (!window.IntersectionObserver) { for (var i = 0; i < items.length; i++) items[i].classList.add('in'); return; }
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
  }, { rootMargin: '0px 0px -12% 0px' });
  items.forEach(function (el) { io.observe(el); });
})();
</script>
