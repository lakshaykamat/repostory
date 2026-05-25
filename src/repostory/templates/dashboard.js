const D = {{DATA}};

// Zinc grayscale: empty → dark
const HM_COLORS = ['#f4f4f5','#d4d4d8','#a1a1aa','#52525b','#09090b'];

// Monochrome shades for donut slices
const CONV_COLORS = {
  feat:'#09090b', fix:'#27272a', refactor:'#3f3f46', chore:'#52525b',
  test:'#71717a', docs:'#a1a1aa', style:'#d4d4d8',  perf:'#18181b',
  ci:'#1c1c1c',  build:'#6b7280', other:'#e4e4e7'
};

// Dark → light for size bars
const SIZE_COLORS = ['#09090b','#27272a','#3f3f46','#71717a','#a1a1aa'];

const C = {
  primary:   '#09090b',
  secondary: '#a1a1aa',
  muted:     '#e4e4e7',
  mid:       '#71717a',
};

const tip = document.getElementById('tip');
const moveTip = e => { tip.style.left = (e.clientX+14)+'px'; tip.style.top = (e.clientY-32)+'px'; };
const showTip = (e, html) => { tip.innerHTML = html; tip.style.display = 'block'; moveTip(e); };
const hideTip = () => tip.style.display = 'none';
document.addEventListener('mousemove', e => { if (tip.style.display !== 'none') moveTip(e); });

function hmColor(count, max) {
  if (!count) return HM_COLORS[0];
  const r = count / max;
  return r < .15 ? HM_COLORS[1] : r < .35 ? HM_COLORS[2] : r < .65 ? HM_COLORS[3] : HM_COLORS[4];
}

function svgEl(tag, attrs = {}) {
  const el = document.createElementNS('http://www.w3.org/2000/svg', tag);
  Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v));
  return el;
}

function svgTxt(text, x, y, attrs = {}) {
  const el = svgEl('text', {x, y, ...attrs});
  el.textContent = text;
  return el;
}

let cur = '__all__';
const data = () => cur === '__all__' ? D.all : D.authors[cur];

// ── KPIs ──
function renderKPIs() {
  const s = data().stats;
  const velArrow = {up:'↑', down:'↓', stable:'→'}[s.velTrend];
  const items = [
    {l:'total commits',   v:s.total.toLocaleString(),               s:'no merges'},
    {l:'peak hour',       v:String(s.peakHour).padStart(2,'0')+':00', s:'most commits'},
    {l:'peak weekday',    v:D.days[s.peakDay],                      s:'busiest day'},
    {l:'peak date',       v:s.peakDate,                             s:s.peakDateCount+' commits'},
    {l:'best streak',     v:s.streak+'d',                           s:'consecutive days'},
    {l:'project age',     v:s.spanLabel,                            s:s.spanDays+' calendar days'},
    {l:'rework rate',     v:s.reworkRate+'%',                       s:s.revertCount+' reverts'},
    {l:'consistency',     v:s.consistency+'%',                      s:'weekly rhythm'},
    {l:'night owl',       v:s.nightPct+'%',                         s:'22:00–04:00'},
    {l:'weekend',         v:s.weekendPct+'%',                       s:'sat + sun'},
    ...(s.hasStat ? [
      {l:'avg commit size', v:s.avgSize+' lines',                   s:'added+deleted'},
      {l:'lines added',     v:(s.totalAdded/1000).toFixed(1)+'k',  s:(s.totalDeleted/1000).toFixed(1)+'k deleted'},
    ] : []),
  ];
  document.getElementById('kpis').innerHTML = items.map((k, i) =>
    `<div class="kpi" style="animation-delay:${i*.025}s">
      <div class="kpi-label">${k.l}</div>
      <div class="kpi-value">${k.v}</div>
      <div class="kpi-sub">${k.s}</div>
    </div>`
  ).join('');
  const vb = document.getElementById('vel-badge');
  if (vb) vb.textContent = velArrow + ' ' + s.velTrend;
}

// ── Heatmap ──
function renderHeatmap() {
  const hm = data().heatmap;
  const max = Math.max(...hm.map(r => r.count), 1);
  const grid = document.getElementById('heatmap');
  grid.innerHTML = '';
  grid.insertAdjacentHTML('beforeend', '<div class="hm-corner"></div>');
  for (let h = 0; h < 24; h++)
    grid.insertAdjacentHTML('beforeend', `<div class="hm-hour-label">${h%4===0 ? String(h).padStart(2,'0') : ''}</div>`);
  D.days.forEach((name, di) => {
    grid.insertAdjacentHTML('beforeend', `<div class="hm-day-label">${name}</div>`);
    for (let h = 0; h < 24; h++) {
      const entry = hm.find(r => r.day===di && r.hour===h);
      const cnt = entry ? entry.count : 0;
      const el = document.createElement('div');
      el.className = 'hm-cell';
      el.style.background = hmColor(cnt, max);
      el.addEventListener('mouseenter', ev => showTip(ev, `${name} ${String(h).padStart(2,'0')}:00 &mdash; ${cnt} commit${cnt!==1?'s':''}`));
      el.addEventListener('mouseleave', hideTip);
      grid.appendChild(el);
    }
  });
  document.getElementById('hm-legend').innerHTML = HM_COLORS.map(c => `<span style="background:${c}"></span>`).join('');
}

// ── Hour bars ──
function renderHourChart() {
  const svg = document.getElementById('hour-svg');
  svg.innerHTML = '';
  const hl = data().hourly;
  const W=380, H=160, pl=28, pr=8, pt=8, pb=24, cw=W-pl-pr, ch=H-pt-pb;
  const max = Math.max(...hl.map(r => r.count), 1);
  const peak = Math.max(...hl.map(r => r.count));
  const bw = (cw/24)*.7, gap = (cw/24)*.3;
  svg.appendChild(svgEl('line', {x1:pl, y1:pt+ch, x2:pl+cw, y2:pt+ch, stroke:'#e4e4e7'}));
  hl.forEach(r => {
    const x = pl + r.hour*(cw/24) + gap/2;
    const bh = Math.max((r.count/max)*ch, 1), y = pt+ch-bh;
    const rect = svgEl('rect', {x, y, width:bw, height:bh, fill: r.count===peak ? C.primary : C.secondary, rx:'1'});
    rect.addEventListener('mouseenter', ev => showTip(ev, `${String(r.hour).padStart(2,'0')}:00 &mdash; ${r.count}`));
    rect.addEventListener('mouseleave', hideTip);
    svg.appendChild(rect);
    if (r.hour%6===0)
      svg.appendChild(svgTxt(String(r.hour).padStart(2,'0'), x+bw/2, pt+ch+14, {'text-anchor':'middle','class':'axis-text'}));
  });
}

// ── Day bars ──
function renderDayChart() {
  const svg = document.getElementById('day-svg');
  svg.innerHTML = '';
  const dl = data().daily;
  const W=380, H=160, pl=28, pr=8, pt=8, pb=24, cw=W-pl-pr, ch=H-pt-pb;
  const max = Math.max(...dl.map(r => r.count), 1);
  const peak = Math.max(...dl.map(r => r.count));
  const bw = (cw/7)*.6, gap = (cw/7)*.4;
  svg.appendChild(svgEl('line', {x1:pl, y1:pt+ch, x2:pl+cw, y2:pt+ch, stroke:'#e4e4e7'}));
  dl.forEach((r, i) => {
    const x = pl + i*(cw/7) + gap/2;
    const bh = Math.max((r.count/max)*ch, 1), y = pt+ch-bh;
    const fill = r.count===peak ? C.primary : i>=5 ? C.mid : C.secondary;
    const rect = svgEl('rect', {x, y, width:bw, height:bh, fill, rx:'2'});
    rect.addEventListener('mouseenter', ev => showTip(ev, `${r.name} &mdash; ${r.count}`));
    rect.addEventListener('mouseleave', hideTip);
    svg.appendChild(rect);
    svg.appendChild(svgTxt(r.name, x+bw/2, pt+ch+14, {'text-anchor':'middle','class':'axis-text'}));
  });
}

// ── Weekly trend ──
function renderWeekly() {
  const svg = document.getElementById('weekly-svg');
  svg.innerHTML = '';
  const wl = data().weekly, rl = data().rolling;
  if (!wl || !wl.length) return;
  const W=900, H=200, pl=40, pr=16, pt=16, pb=28, cw=W-pl-pr, ch=H-pt-pb;
  const max = Math.max(...wl.map(r => r.count), 1);
  const n = wl.length;

  [0,.25,.5,.75,1].forEach(f => {
    const y = pt+ch*(1-f);
    svg.appendChild(svgEl('line', {x1:pl, y1:y, x2:pl+cw, y2:y, stroke:'#e4e4e7'}));
    if (f > 0) svg.appendChild(svgTxt(Math.round(max*f), pl-4, y+3, {'text-anchor':'end','class':'axis-text'}));
  });

  const pts = wl.map((r,i) => [pl+(i/(n-1||1))*cw, pt+ch*(1-r.count/max)]);
  const areaPath = 'M'+pts[0][0]+','+(pt+ch)+' '+pts.map(p=>p[0]+','+p[1]).join(' ')+' '+pts[n-1][0]+','+(pt+ch)+' Z';
  svg.appendChild(svgEl('path', {d:areaPath, fill:C.primary, opacity:'.05'}));
  svg.appendChild(svgEl('path', {d:'M'+pts.map(p=>p.join(',')).join(' L'), fill:'none', stroke:C.primary, 'stroke-width':'1.5', 'stroke-linejoin':'round'}));

  if (rl && rl.length) {
    const rpts = rl.map((r,i) => [pl+(i/(n-1||1))*cw, pt+ch*(1-r.avg/max)]);
    svg.appendChild(svgEl('path', {d:'M'+rpts.map(p=>p.join(',')).join(' L'), fill:'none', stroke:C.mid, 'stroke-width':'1.5', 'stroke-dasharray':'4 3', 'stroke-linejoin':'round'}));
  }

  const peakV = Math.max(...wl.map(r => r.count));
  wl.forEach((r,i) => {
    const [x, y] = pts[i];
    if (r.count === peakV) {
      svg.appendChild(svgEl('circle', {cx:x, cy:y, r:'4', fill:C.primary}));
      svg.appendChild(svgTxt(r.count, x, y-8, {'text-anchor':'middle', fill:C.primary, 'font-family':'monospace', 'font-size':'11'}));
    }
  });

  const step = Math.max(1, Math.round(n/8));
  wl.forEach((r,i) => {
    if (i%step===0) svg.appendChild(svgTxt(r.week.slice(5), pts[i][0], pt+ch+16, {'text-anchor':'middle','class':'axis-text'}));
  });

  svg.appendChild(svgTxt('commits', pl, pt+8, {fill:C.primary, 'font-family':'monospace', 'font-size':'10'}));
  svg.appendChild(svgTxt('4w avg', pl+60, pt+8, {fill:C.mid, 'font-family':'monospace', 'font-size':'10'}));
}

// ── Monthly ──
function renderMonthly() {
  const svg = document.getElementById('monthly-svg');
  svg.innerHTML = '';
  const ml = data().monthly;
  if (!ml || !ml.length) return;
  const W=900, H=170, pl=40, pr=16, pt=10, pb=28, cw=W-pl-pr, ch=H-pt-pb;
  const max = Math.max(...ml.map(r => r.count), 1);
  const n = ml.length;
  const bw = Math.min((cw/n)*.75, 42), slot = cw/n;

  svg.appendChild(svgEl('line', {x1:pl, y1:pt+ch, x2:pl+cw, y2:pt+ch, stroke:'#e4e4e7'}));
  ml.forEach((r,i) => {
    const x = pl + i*slot + (slot-bw)/2;
    const bh = Math.max((r.count/max)*ch, 1), y = pt+ch-bh;
    const rect = svgEl('rect', {x, y, width:bw, height:bh, fill: r.count===max ? C.primary : C.secondary, rx:'2'});
    rect.addEventListener('mouseenter', ev => showTip(ev, `${r.month} &mdash; ${r.count} commits`));
    rect.addEventListener('mouseleave', hideTip);
    svg.appendChild(rect);
    if (i%3===0||n<=18) svg.appendChild(svgTxt(r.label, x+bw/2, pt+ch+14, {'text-anchor':'middle','class':'axis-text'}));
  });

  const pk = ml.find(r => r.count===max);
  if (pk) {
    const i = ml.indexOf(pk), x = pl+i*slot+(slot-bw)/2+bw/2, bh = (pk.count/max)*ch;
    svg.appendChild(svgTxt(pk.count, x, pt+ch-bh-6, {'text-anchor':'middle', fill:C.primary, 'font-family':'monospace', 'font-size':'11'}));
  }
}

// ── Commit type donut ──
function renderConvTypes() {
  const ct = data().convTypes;
  const el = document.getElementById('conv-panel');
  if (!ct || !Object.keys(ct).length) {
    el.innerHTML = '<div style="font-family:monospace;font-size:12px;color:#71717a">No conventional commit prefixes found</div>';
    return;
  }
  const total = Object.values(ct).reduce((s,v) => s+v, 0);
  const sorted = Object.entries(ct).sort(([,a],[,b]) => b-a);
  const R=70, r=42, cx=80, cy=80;

  let svgStr = `<svg viewBox="0 0 160 160" style="width:160px;height:160px;flex-shrink:0">`;
  let angle = -Math.PI/2;
  sorted.forEach(([key,val]) => {
    const sweep = (val/total)*Math.PI*2;
    if (sweep < 0.01) { angle += sweep; return; }
    const x1=cx+Math.cos(angle)*R, y1=cy+Math.sin(angle)*R;
    const x2=cx+Math.cos(angle+sweep)*R, y2=cy+Math.sin(angle+sweep)*R;
    const ix1=cx+Math.cos(angle)*r, iy1=cy+Math.sin(angle)*r;
    const ix2=cx+Math.cos(angle+sweep)*r, iy2=cy+Math.sin(angle+sweep)*r;
    const large = sweep > Math.PI ? 1 : 0;
    const col = CONV_COLORS[key] || '#a1a1aa';
    svgStr += `<path d="M ${x1} ${y1} A ${R} ${R} 0 ${large} 1 ${x2} ${y2} L ${ix2} ${iy2} A ${r} ${r} 0 ${large} 0 ${ix1} ${iy1} Z" fill="${col}"><title>${key}: ${val}</title></path>`;
    angle += sweep;
  });
  const topType = sorted[0];
  svgStr += `<text x="${cx}" y="${cy-4}" text-anchor="middle" fill="#09090b" font-family="monospace" font-size="18" font-weight="600">${topType ? Math.round(topType[1]/total*100) : 0}%</text>`;
  svgStr += `<text x="${cx}" y="${cy+14}" text-anchor="middle" fill="#71717a" font-family="monospace" font-size="9">${topType ? topType[0] : ''}</text>`;
  svgStr += '</svg>';

  const legend = sorted.map(([key,val]) =>
    `<div class="conv-row">
      <div class="conv-dot" style="background:${CONV_COLORS[key]||'#a1a1aa'}"></div>
      ${key}
      <div class="conv-pct">${Math.round(val/total*100)}%&nbsp;<span style="color:#a1a1aa">${val}</span></div>
    </div>`
  ).join('');

  el.innerHTML = `<div class="conv-donut-wrap">${svgStr}<div class="conv-legend">${legend}</div></div>`;
}

// ── Rework rate ──
function renderRework() {
  const s = data().stats;
  const el = document.getElementById('rework-panel');
  const rate = s.reworkRate;
  const verdict = rate > 30 ? "High — code shipping before it's ready"
                : rate > 15 ? "Moderate — worth watching"
                : "Healthy";
  el.innerHTML = `
    <div class="rework-big">${rate}<span style="font-size:28px;font-weight:400">%</span></div>
    <div style="font-family:monospace;font-size:11px;color:#71717a;margin-top:6px">${verdict}</div>
    <div class="rework-bar-wrap"><div class="rework-bar" style="width:${Math.min(rate,100)}%"></div></div>
    <div class="signal-row"><span class="signal-label">fix/bug commits</span><span>${s.reworkRate}%</span></div>
    <div class="signal-row"><span class="signal-label">explicit reverts</span><span>${s.revertCount}</span></div>
    <div class="signal-row"><span class="signal-label">consistency score</span><span>${s.consistency}%</span></div>
    <div class="signal-row"><span class="signal-label">velocity trend</span><span>${s.velTrend==='up'?'↑ accelerating':s.velTrend==='down'?'↓ slowing':'→ stable'}</span></div>`;
}

// ── Commit size ──
function renderSizeDist() {
  const sd = data().sizeDist;
  const el = document.getElementById('size-panel');
  const badge = document.getElementById('stat-badge');
  if (!sd || !sd.length) {
    el.innerHTML = '<div style="font-family:monospace;font-size:12px;color:#71717a">Run without --fast to enable</div>';
    if (badge) badge.textContent = '--fast mode';
    return;
  }
  if (badge) badge.textContent = 'lines added+deleted';
  const max = Math.max(...sd.map(r => r.count), 1);
  el.innerHTML = sd.map((r,i) => `
    <div class="size-row">
      <div class="size-label">${r.label}</div>
      <div class="size-bar-wrap"><div class="size-bar" style="width:${Math.round(r.count/max*100)}%;background:${SIZE_COLORS[i]}"></div></div>
      <div class="size-count">${r.count}</div>
    </div>`).join('');
  const s = data().stats;
  if (s.avgSize) el.innerHTML += `<div style="font-family:monospace;font-size:11px;color:#71717a;margin-top:16px;padding-top:16px;border-top:1px solid #e4e4e7">avg <b style="color:#09090b">${s.avgSize} lines</b> per commit</div>`;
}

// ── Message quality ──
function renderMsgQuality() {
  const el = document.getElementById('msg-panel');
  const mb = data().msgBins, s = data().stats;
  const max = Math.max(...mb.map(r => r.count), 1);
  el.innerHTML = mb.map(r => `
    <div class="msg-row">
      <div class="msg-label">${r.label}</div>
      <div class="msg-bar-wrap"><div class="msg-bar" style="width:${Math.round(r.count/max*100)}%"></div></div>
      <div class="msg-count">${r.count}</div>
    </div>`).join('');
  el.innerHTML += `
    <div class="msg-stat-row">
      <div class="msg-stat"><span>avg length</span><b>${s.msgAvgLen} chars</b></div>
      <div class="msg-stat"><span>lazy commits</span><b>${s.msgLazyPct}%</b></div>
    </div>`;
}

// ── Bus factor ──
function renderBusFactor() {
  const bf = data().busFactor;
  const el = document.getElementById('bus-panel');
  if (!bf || !bf.length) {
    el.innerHTML = '<div style="font-family:monospace;font-size:12px;color:#71717a">No file data — run without --fast</div>';
    return;
  }
  const maxC = Math.max(...bf.map(r => r.commits), 1);
  el.innerHTML = bf.map(r => {
    const fill = r.authors === 1 ? '#3f3f46' : r.authors <= 3 ? '#71717a' : '#09090b';
    const solo = r.authors === 1 ? ` <span style="color:#a1a1aa;font-size:10px">${r.authorList[0].split('@')[0]}</span>` : '';
    return `<div class="bf-row">
      <div class="bf-dir">${r.dir}</div>
      <div class="bf-bar-wrap"><div class="bf-bar" style="width:${Math.round(r.commits/maxC*100)}%;background:${fill};opacity:.5"></div></div>
      <div class="bf-authors" style="color:${fill}">${r.authors} author${r.authors!==1?'s':''}${solo}</div>
      <div class="bf-commits">${r.commits}</div>
    </div>`;
  }).join('');
}

// ── Author × directory matrix ──
function renderAuthorDir() {
  const adm = data().authorDirMatrix, dirs = data().dirList;
  const svg = document.getElementById('adm-svg');
  svg.innerHTML = '';
  if (!adm || !adm.length || !dirs || !dirs.length) {
    svg.setAttribute('viewBox', '0 0 400 40');
    svg.appendChild(svgTxt('No file data — run without --fast', 10, 20, {fill:'#71717a','font-family':'monospace','font-size':'12'}));
    return;
  }
  const CW=64, CH=22, PL=130, PT=56, GAP=2;
  const W = PL + dirs.length*(CW+GAP) + 20;
  const H = PT + adm.length*(CH+GAP) + 20;
  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  svg.style.minWidth = W+'px';

  const maxV = Math.max(...adm.flatMap(r => dirs.map(d => r.dirs[d]||0)), 1);

  dirs.forEach((d,i) => {
    const x = PL + i*(CW+GAP) + CW/2;
    const t = svgTxt(d.slice(-10), x, PT-10, {'text-anchor':'start','class':'axis-text', transform:`rotate(-35,${x},${PT-10})`});
    svg.appendChild(t);
  });

  adm.forEach((row, ri) => {
    const y = PT + ri*(CH+GAP);
    svg.appendChild(svgTxt(row.author.split('@')[0].slice(0,18), PL-8, y+CH*.72, {'text-anchor':'end','class':'axis-text'}));
    dirs.forEach((d, ci) => {
      const val = row.dirs[d]||0;
      const x = PL + ci*(CW+GAP);
      const alpha = val ? Math.max(0.08, val/maxV) : 0;
      const fill = val ? `rgba(9,9,11,${alpha.toFixed(2)})` : '#f4f4f5';
      const rect = svgEl('rect', {x, y, width:CW, height:CH, rx:'2', fill});
      if (val) {
        rect.addEventListener('mouseenter', ev => showTip(ev, `${row.author.split('@')[0]} × ${d}: ${val} commits`));
        rect.addEventListener('mouseleave', hideTip);
        svg.appendChild(rect);
        svg.appendChild(svgTxt(val, x+CW/2, y+CH*.72, {'text-anchor':'middle', fill: alpha > 0.5 ? '#fff' : '#3f3f46', 'font-family':'monospace', 'font-size':'9'}));
      } else {
        svg.appendChild(rect);
      }
    });
  });
  svg.appendChild(svgTxt('dim = fewer commits, bright = more', PL, H-8, {fill:'#a1a1aa','font-family':'monospace','font-size':'9'}));
}

// ── Calendar heatmap ──
function renderCalendar() {
  const svg = document.getElementById('cal-svg');
  svg.innerHTML = '';
  const byDate = {};
  data().calendar.forEach(r => byDate[r.date] = r.count);
  const maxC = Math.max(...Object.values(byDate), 1);
  const WEEKS=53, CW=14, CH=14, GAP=2, PL=28, PT=22;
  const today = new Date();
  const start = new Date(today);
  start.setDate(today.getDate() - (WEEKS*7-1));
  start.setDate(start.getDate() - start.getDay());

  let lastMonth = -1;
  for (let w = 0; w < WEEKS; w++) {
    const d = new Date(start);
    d.setDate(start.getDate() + w*7);
    if (d.getMonth() !== lastMonth) {
      lastMonth = d.getMonth();
      svg.appendChild(svgTxt(D.months[lastMonth], PL+w*(CW+GAP), 12, {'class':'axis-text'}));
    }
  }

  ['S','M','T','W','T','F','S'].forEach((n,i) => {
    if (i%2===1) svg.appendChild(svgTxt(n, 0, PT+i*(CH+GAP)+CH*.75, {'class':'axis-text'}));
  });

  for (let w = 0; w < WEEKS; w++) {
    for (let d = 0; d < 7; d++) {
      const date = new Date(start);
      date.setDate(start.getDate() + w*7 + d);
      if (date > today) continue;
      const ds = date.toISOString().slice(0,10);
      const cnt = byDate[ds]||0;
      const x = PL+w*(CW+GAP), y = PT+d*(CH+GAP);
      const rect = svgEl('rect', {x, y, width:CW, height:CH, rx:'2', fill:hmColor(cnt,maxC)});
      if (cnt) {
        rect.addEventListener('mouseenter', ev => showTip(ev, `${ds} — ${cnt} commit${cnt!==1?'s':''}`));
        rect.addEventListener('mouseleave', hideTip);
      }
      svg.appendChild(rect);
    }
  }
}

// ── Tag timeline ──
function renderTagTimeline() {
  const tags = D.tags;
  const panel = document.getElementById('tag-panel');
  if (!tags || !tags.length) { panel.style.display='none'; return; }
  panel.style.display = 'block';
  document.getElementById('tag-count-badge').textContent = tags.length+' tags';
  const svg = document.getElementById('tag-svg');
  svg.innerHTML = '';
  const W=900, H=100, pl=20, pr=20, mid=H/2;
  const dates = tags.map(t => new Date(t.date).getTime());
  const minD = Math.min(...dates), maxD = Math.max(...dates);
  const span = maxD-minD||1;
  svg.appendChild(svgEl('line', {x1:pl, y1:mid, x2:W-pr, y2:mid, stroke:'#e4e4e7','stroke-width':'1'}));
  tags.forEach((t,i) => {
    const x = pl + ((new Date(t.date).getTime()-minD)/span)*(W-pl-pr);
    const above = i%2===0;
    svg.appendChild(svgEl('line', {x1:x, y1:mid-6, x2:x, y2:mid+6, stroke:'#09090b','stroke-width':'1'}));
    const dot = svgEl('circle', {cx:x, cy:mid, r:'3', fill:'#09090b'});
    dot.addEventListener('mouseenter', ev => showTip(ev, `${t.name} — ${t.date}`));
    dot.addEventListener('mouseleave', hideTip);
    svg.appendChild(dot);
    svg.appendChild(svgTxt(t.name, x, above?mid-14:mid+22, {'text-anchor':'middle',fill:'#09090b','font-family':'monospace','font-size':'9'}));
  });
}

// ── Top dates ──
function renderTopDates() {
  const td = data().topDates;
  const max = td[0] ? td[0].count : 1;
  document.getElementById('top-dates').innerHTML = td.map((r,i) =>
    `<div class="td-row">
      <div class="td-rank">${i+1}</div>
      <div><span class="td-date">${r.date}</span><span class="td-day">${r.dayName}</span></div>
      <div class="td-right">
        <div class="td-bar-wrap"><div class="td-bar" style="width:${Math.round(r.count/max*100)}%"></div></div>
        <div class="td-count">${r.count}</div>
      </div>
    </div>`
  ).join('');
}

// ── File hotspots ──
function renderHotspotFiles() {
  const el = document.getElementById('hotspot-panel');
  const files = data().hotspotFiles;
  if (!files || !files.length) {
    el.innerHTML = '<div style="font-family:monospace;font-size:12px;color:#71717a">Run without --fast to enable</div>';
    return;
  }
  const maxC = files[0].commits;
  el.innerHTML = files.map(f => {
    const pct  = Math.round(f.commits / maxC * 100);
    const name = f.path.length > 44 ? '...' + f.path.slice(-41) : f.path;
    const solo = f.authors === 1 ? ' <span style="color:#a1a1aa">solo</span>' : '';
    return `<div style="display:grid;grid-template-columns:1fr 72px 36px;align-items:center;gap:8px;padding:5px 0;border-bottom:1px solid #e4e4e7">
      <div style="font-family:monospace;font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#3f3f46" title="${f.path}">${name}${solo}</div>
      <div style="height:3px;background:#f4f4f5;border-radius:2px;overflow:hidden"><div style="height:100%;width:${pct}%;background:#09090b;border-radius:2px"></div></div>
      <div style="font-family:monospace;font-size:10px;color:#71717a;text-align:right">${f.commits}</div>
    </div>`;
  }).join('');
}

// ── Co-change coupling ──
function renderCoChangeCoupling() {
  const el = document.getElementById('coupling-panel');
  const pairs = D.all.coupledFiles;
  if (!pairs || !pairs.length) {
    el.innerHTML = '<div style="font-family:monospace;font-size:12px;color:#71717a">No strong coupling found, or run without --fast</div>';
    return;
  }
  el.innerHTML = pairs.map(p => {
    const shortA = p.a.length > 32 ? '...' + p.a.slice(-29) : p.a;
    const shortB = p.b.length > 32 ? '...' + p.b.slice(-29) : p.b;
    const col    = p.pct > 70 ? '#09090b' : p.pct > 40 ? '#3f3f46' : '#71717a';
    return `<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;padding:8px 0;border-bottom:1px solid #e4e4e7">
      <div>
        <div style="font-family:monospace;font-size:11px;color:#3f3f46" title="${p.a}">${shortA}</div>
        <div style="font-family:monospace;font-size:10px;color:#a1a1aa;margin:2px 0">+</div>
        <div style="font-family:monospace;font-size:11px;color:#3f3f46" title="${p.b}">${shortB}</div>
      </div>
      <div style="text-align:right;flex-shrink:0">
        <div style="font-size:20px;font-weight:600;color:${col}">${p.pct}%</div>
        <div style="font-family:monospace;font-size:10px;color:#a1a1aa">${p.count} commits</div>
      </div>
    </div>`;
  }).join('');
}

// ── Gini + Lorenz ──
function renderGiniLorenz() {
  const el = document.getElementById('gini-panel');
  const gini   = D.all.gini;
  const lorenz = D.all.lorenz;
  const W=160, H=160, pad=16, cw=W-pad*2, ch=H-pad*2;
  let svgStr = `<svg viewBox="0 0 ${W} ${H}" style="width:${W}px;height:${H}px;flex-shrink:0;border:1px solid #e4e4e7;border-radius:4px">`;
  // equality diagonal
  svgStr += `<line x1="${pad}" y1="${pad+ch}" x2="${pad+cw}" y2="${pad}" stroke="#e4e4e7" stroke-width="1"/>`;
  if (lorenz && lorenz.length) {
    const pts = lorenz.map(p => [pad+p.x/100*cw, pad+ch-p.y/100*ch]);
    svgStr += `<path d="M${pad},${pad+ch} ${pts.map(p=>p.join(',')).join(' L')}" fill="#09090b" opacity=".07"/>`;
    svgStr += `<path d="M${pts.map(p=>p.join(',')).join(' L')}" fill="none" stroke="#09090b" stroke-width="1.5"/>`;
  }
  svgStr += '</svg>';
  const verdict = gini < 0.35 ? 'Well distributed'
                : gini < 0.6  ? 'Moderately concentrated'
                : 'Highly concentrated';
  el.innerHTML = `
    <div style="display:flex;gap:20px;align-items:flex-start">
      ${svgStr}
      <div>
        <div style="font-size:48px;font-weight:600;letter-spacing:-.04em;line-height:1">${gini.toFixed(2)}</div>
        <div style="font-family:monospace;font-size:10px;color:#71717a;margin-top:4px">Gini coefficient</div>
        <div style="font-family:monospace;font-size:11px;color:#09090b;margin-top:16px">${verdict}</div>
        <div style="font-family:monospace;font-size:10px;color:#a1a1aa;margin-top:4px">0 = equal &nbsp; 1 = one person</div>
      </div>
    </div>`;
}

// ── Author tenure ──
function renderAuthorTenure() {
  const svg    = document.getElementById('tenure-svg');
  svg.innerHTML = '';
  const tenure = D.all.authorTenure;
  if (!tenure || !tenure.length) {
    svg.setAttribute('viewBox','0 0 400 40');
    svg.appendChild(svgTxt('No data',10,20,{fill:'#71717a','font-family':'monospace','font-size':'12'}));
    return;
  }
  const PL=140, PR=48, PT=8, ROW=26, W=520;
  const H   = PT + tenure.length * ROW + PT;
  const cw  = W - PL - PR;
  const now = Date.now();
  const minDate = new Date(tenure[0].first).getTime();
  const span    = Math.max(now - minDate, 1);
  const toX     = d => PL + (new Date(d).getTime() - minDate) / span * cw;
  const ACTIVE  = 90 * 86400000;

  svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
  svg.style.height = H + 'px';

  // today line
  svg.appendChild(svgEl('line',{x1:PL+cw,y1:PT,x2:PL+cw,y2:H-PT,stroke:'#e4e4e7','stroke-dasharray':'3 3'}));
  svg.appendChild(svgTxt('today',PL+cw-3,PT+9,{'text-anchor':'end',fill:'#a1a1aa','font-family':'monospace','font-size':'8'}));

  tenure.forEach((t,i) => {
    const y      = PT + i * ROW;
    const x1     = toX(t.first);
    const x2     = toX(t.last);
    const active = (now - new Date(t.last).getTime()) < ACTIVE;
    svg.appendChild(svgTxt(t.author.split('@')[0].slice(0,20), PL-6, y+ROW*.68, {'text-anchor':'end','class':'axis-text'}));
    svg.appendChild(svgEl('rect',{x:x1, y:y+5, width:Math.max(x2-x1,3), height:ROW-10, fill:active?'#09090b':'#d4d4d8', rx:'2'}));
    svg.appendChild(svgTxt(t.commits, W-PR+6, y+ROW*.68, {'class':'axis-text'}));
  });
}

// ── New contributor cohorts ──
function renderContributorCohorts() {
  const svg  = document.getElementById('cohorts-svg');
  svg.innerHTML = '';
  const cohorts = D.all.contributorCohorts;
  if (!cohorts || !cohorts.length) return;
  const W=900, H=140, pl=36, pr=16, pt=10, pb=28, cw=W-pl-pr, ch=H-pt-pb;
  const max = Math.max(...cohorts.map(r=>r.count), 1);
  const n   = cohorts.length;
  const bw  = Math.min((cw/n)*.75, 36), slot = cw/n;
  svg.appendChild(svgEl('line',{x1:pl,y1:pt+ch,x2:pl+cw,y2:pt+ch,stroke:'#e4e4e7'}));
  cohorts.forEach((r,i) => {
    const x  = pl + i*slot + (slot-bw)/2;
    const bh = Math.max((r.count/max)*ch, 1), y = pt+ch-bh;
    const rect = svgEl('rect',{x,y,width:bw,height:bh,fill:'#09090b',rx:'2'});
    rect.addEventListener('mouseenter', ev => showTip(ev, `${r.month} — ${r.count} new contributor${r.count!==1?'s':''}`));
    rect.addEventListener('mouseleave', hideTip);
    svg.appendChild(rect);
    if (r.count > 0) svg.appendChild(svgTxt(r.count, x+bw/2, y-5, {'text-anchor':'middle',fill:'#09090b','font-family':'monospace','font-size':'10'}));
    if (i%Math.max(1,Math.round(n/8))===0) svg.appendChild(svgTxt(r.month.slice(5)+'/'+r.month.slice(2,4), x+bw/2, pt+ch+16, {'text-anchor':'middle','class':'axis-text'}));
  });
}

// ── Work-life balance trend ──
function renderWLBTrend() {
  const svg  = document.getElementById('wlb-svg');
  svg.innerHTML = '';
  const wlb = data().wlbTrend;
  if (!wlb || wlb.length < 2) { svg.appendChild(svgTxt('Not enough data',10,20,{fill:'#71717a','font-family':'monospace','font-size':'12'})); return; }
  const W=500, H=180, pl=36, pr=16, pt=20, pb=28, cw=W-pl-pr, ch=H-pt-pb;
  const n   = wlb.length;
  const toX = i => pl + (i/(n-1||1))*cw;

  [0,25,50,75,100].forEach(f => {
    const y = pt+ch*(1-f/100);
    svg.appendChild(svgEl('line',{x1:pl,y1:y,x2:pl+cw,y2:y,stroke:'#e4e4e7'}));
    svg.appendChild(svgTxt(f+'%', pl-4, y+3, {'text-anchor':'end','class':'axis-text'}));
  });

  const nightPts  = wlb.map((r,i) => [toX(i), pt+ch*(1-r.nightPct/100)]);
  const wkndPts   = wlb.map((r,i) => [toX(i), pt+ch*(1-r.weekendPct/100)]);
  svg.appendChild(svgEl('path',{d:'M'+nightPts.map(p=>p.join(',')).join(' L'), fill:'none', stroke:'#09090b', 'stroke-width':'1.5', 'stroke-linejoin':'round'}));
  svg.appendChild(svgEl('path',{d:'M'+wkndPts.map(p=>p.join(',')).join(' L'),  fill:'none', stroke:'#71717a', 'stroke-width':'1.5', 'stroke-dasharray':'4 3', 'stroke-linejoin':'round'}));

  const step = Math.max(1, Math.round(n/6));
  wlb.forEach((r,i) => { if (i%step===0) svg.appendChild(svgTxt(r.month.slice(5)+'/'+r.month.slice(2,4), toX(i), pt+ch+16, {'text-anchor':'middle','class':'axis-text'})); });

  svg.appendChild(svgTxt('night (22-04)', pl, pt-6, {fill:'#09090b','font-family':'monospace','font-size':'10'}));
  svg.appendChild(svgTxt('weekend', pl+110, pt-6, {fill:'#71717a','font-family':'monospace','font-size':'10'}));
}

// ── Commit message length trend ──
function renderMsgTrend() {
  const svg  = document.getElementById('msg-trend-svg');
  svg.innerHTML = '';
  const trend = data().msgTrend;
  if (!trend || trend.length < 2) { svg.appendChild(svgTxt('Not enough data',10,20,{fill:'#71717a','font-family':'monospace','font-size':'12'})); return; }
  const W=500, H=180, pl=36, pr=16, pt=20, pb=28, cw=W-pl-pr, ch=H-pt-pb;
  const max = Math.max(...trend.map(r=>r.avgLen), 1);
  const n   = trend.length;

  [0,.25,.5,.75,1].forEach(f => {
    const y = pt+ch*(1-f);
    svg.appendChild(svgEl('line',{x1:pl,y1:y,x2:pl+cw,y2:y,stroke:'#e4e4e7'}));
    if (f>0) svg.appendChild(svgTxt(Math.round(max*f), pl-4, y+3, {'text-anchor':'end','class':'axis-text'}));
  });

  const pts  = trend.map((r,i) => [pl+(i/(n-1||1))*cw, pt+ch*(1-r.avgLen/max)]);
  const area = 'M'+pts[0][0]+','+(pt+ch)+' '+pts.map(p=>p.join(',')).join(' ')+' '+pts[n-1][0]+','+(pt+ch)+' Z';
  svg.appendChild(svgEl('path',{d:area, fill:'#09090b', opacity:'.05'}));
  svg.appendChild(svgEl('path',{d:'M'+pts.map(p=>p.join(',')).join(' L'), fill:'none', stroke:'#09090b','stroke-width':'1.5','stroke-linejoin':'round'}));

  // 50-char reference line
  const refY = pt+ch*(1-50/max);
  if (refY > pt && refY < pt+ch) {
    svg.appendChild(svgEl('line',{x1:pl,y1:refY,x2:pl+cw,y2:refY,stroke:'#d4d4d8','stroke-dasharray':'3 3'}));
    svg.appendChild(svgTxt('50 chars', pl+cw, refY-4, {'text-anchor':'end',fill:'#a1a1aa','font-family':'monospace','font-size':'9'}));
  }

  const step = Math.max(1, Math.round(n/6));
  trend.forEach((r,i) => { if (i%step===0) svg.appendChild(svgTxt(r.month.slice(5)+'/'+r.month.slice(2,4), pts[i][0], pt+ch+16, {'text-anchor':'middle','class':'axis-text'})); });
  svg.appendChild(svgTxt('avg message length (chars)', pl, pt-6, {fill:'#09090b','font-family':'monospace','font-size':'10'}));
}

// ── Commit weight by hour ──
function renderHourlySize() {
  const svg = document.getElementById('hourly-size-svg');
  svg.innerHTML = '';
  const hs = data().hourlySize;
  if (!hs || !hs.some(h=>h.avgLines>0)) {
    svg.setAttribute('viewBox','0 0 380 40');
    svg.appendChild(svgTxt('Run without --fast to enable',10,20,{fill:'#71717a','font-family':'monospace','font-size':'12'}));
    return;
  }
  const W=380, H=160, pl=44, pr=8, pt=8, pb=24, cw=W-pl-pr, ch=H-pt-pb;
  const max  = Math.max(...hs.map(r=>r.avgLines), 1);
  const peak = Math.max(...hs.map(r=>r.avgLines));
  const bw   = (cw/24)*.7, gap = (cw/24)*.3;
  [0,.5,1].forEach(f => {
    const y = pt+ch*(1-f);
    svg.appendChild(svgEl('line',{x1:pl,y1:y,x2:pl+cw,y2:y,stroke:'#e4e4e7'}));
    if (f>0) svg.appendChild(svgTxt(Math.round(max*f), pl-3, y+3, {'text-anchor':'end','class':'axis-text'}));
  });
  hs.forEach(r => {
    if (!r.avgLines) return;
    const x    = pl + r.hour*(cw/24) + gap/2;
    const bh   = Math.max((r.avgLines/max)*ch, 1), y = pt+ch-bh;
    const rect = svgEl('rect',{x,y,width:bw,height:bh,fill:r.avgLines===peak?C.primary:C.secondary,rx:'1'});
    rect.addEventListener('mouseenter', ev => showTip(ev, `${String(r.hour).padStart(2,'0')}:00 — avg ${r.avgLines} lines`));
    rect.addEventListener('mouseleave', hideTip);
    svg.appendChild(rect);
    if (r.hour%6===0) svg.appendChild(svgTxt(String(r.hour).padStart(2,'0'), x+bw/2, pt+ch+14, {'text-anchor':'middle','class':'axis-text'}));
  });
}

// ── Release cadence ──
function renderReleaseCadence() {
  const panel = document.getElementById('cadence-panel');
  const rc    = D.cadence;
  if (!rc || !rc.gaps || !rc.gaps.length) { panel.style.display='none'; return; }
  panel.style.display = 'block';
  const el    = document.getElementById('cadence-content');
  const trend = rc.trend==='faster' ? '↑ shipping faster' : rc.trend==='slower' ? '↓ slowing down' : '→ stable';
  const max   = Math.max(...rc.gaps, 1);
  el.innerHTML = `
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:#e4e4e7;border:1px solid #e4e4e7;border-radius:6px;overflow:hidden;margin-bottom:20px">
      <div style="background:#fff;padding:14px"><div style="font-family:monospace;font-size:9px;color:#71717a;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px">median gap</div><div style="font-size:20px;font-weight:600">${rc.median}d</div></div>
      <div style="background:#fff;padding:14px"><div style="font-family:monospace;font-size:9px;color:#71717a;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px">longest gap</div><div style="font-size:20px;font-weight:600">${rc.longest}d</div></div>
      <div style="background:#fff;padding:14px"><div style="font-family:monospace;font-size:9px;color:#71717a;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px">trend</div><div style="font-size:14px;font-weight:600;font-family:monospace">${trend}</div></div>
    </div>
    <div style="font-family:monospace;font-size:9px;color:#a1a1aa;text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px">gap between releases (days)</div>
    <div style="display:flex;align-items:flex-end;gap:3px;height:56px">
      ${rc.gaps.map(g=>`<div style="flex:1;min-width:3px;height:${Math.max(4,Math.round(g/max*52))}px;background:#09090b;border-radius:2px 2px 0 0" title="${g}d"></div>`).join('')}
    </div>`;
}

// ── Directory freshness ──
function renderFileAge() {
  const el  = document.getElementById('file-age-panel');
  const ages = D.all.fileAge;
  if (!ages || !ages.length) {
    el.innerHTML = '<div style="font-family:monospace;font-size:12px;color:#71717a">Run without --fast to enable</div>';
    return;
  }
  const maxDays = Math.max(...ages.map(a=>a.daysSince), 1);
  el.innerHTML = ages.map(a => {
    const pct   = Math.round(a.daysSince/maxDays*100);
    const col   = a.daysSince > 365 ? '#a1a1aa' : a.daysSince > 90 ? '#71717a' : '#09090b';
    const label = a.daysSince > 730 ? `${Math.floor(a.daysSince/365)}y ago`
                : a.daysSince > 60  ? `${Math.floor(a.daysSince/30)}mo ago`
                : `${a.daysSince}d ago`;
    return `<div style="display:grid;grid-template-columns:130px 1fr 80px;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid #e4e4e7">
      <div style="font-family:monospace;font-size:12px">${a.dir}</div>
      <div style="height:3px;background:#f4f4f5;border-radius:2px;overflow:hidden"><div style="height:100%;width:${pct}%;background:${col};border-radius:2px"></div></div>
      <div style="font-family:monospace;font-size:10px;color:${col};text-align:right">${label}</div>
    </div>`;
  }).join('');
}

// ── Tabs ──
function renderTabs() {
  const container = document.getElementById('tabs');
  const authors = Object.keys(D.authors);
  const allBtn = document.createElement('button');
  allBtn.className = 'tab active';
  allBtn.textContent = 'all authors';
  allBtn.onclick = () => switchTo('__all__', allBtn);
  container.appendChild(allBtn);
  if (authors.length > 1) {
    authors.forEach(a => {
      const t = document.createElement('button');
      t.className = 'tab';
      t.textContent = a;
      t.onclick = () => switchTo(a, t);
      container.appendChild(t);
    });
  }
}

function switchTo(author, el) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
  cur = author;
  renderAll();
}

function renderAll() {
  renderKPIs(); renderHeatmap(); renderHourChart(); renderDayChart();
  renderWeekly(); renderMonthly(); renderConvTypes(); renderRework();
  renderSizeDist(); renderMsgQuality(); renderBusFactor(); renderAuthorDir();
  renderHotspotFiles(); renderCoChangeCoupling();
  renderGiniLorenz(); renderAuthorTenure();
  renderContributorCohorts();
  renderWLBTrend(); renderMsgTrend();
  renderHourlySize(); renderReleaseCadence();
  renderFileAge();
  renderCalendar(); renderTopDates();
}

document.getElementById('repo-pill').textContent = D.repo;
document.getElementById('subtitle').textContent = D.dateRange + ' · ' + D.totalCommits.toLocaleString() + ' commits total';
renderTabs();
renderTagTimeline();
renderAll();
