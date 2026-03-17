"""
Build script for Diecast Catalog
- Reads products.xml (raw supplier data)
- Applies 30% markup on cost, rounds up to nearest .99
- Outputs index.html (product grid) + descs.json (lazy-loaded descriptions)

Daily update: just replace products.xml and run this script (or push to GitHub).
"""
import xml.etree.ElementTree as ET
import json, math, html, re, os

# ── PRICING ──────────────────────────────────────────────────────────────────
def markup_price(cost_str):
    try:
        cost = float(cost_str)
        if cost <= 0:
            return ''
        marked = cost * 1.30                  # 30% markup
        rounded = math.ceil(marked) - 0.01   # round up to .99
        if rounded < marked:
            rounded += 1
        return f"{rounded:.2f}"
    except:
        return ''

# ── DESCRIPTION CLEANUP ──────────────────────────────────────────────────────
def clean_desc(raw):
    if not raw:
        return ''
    decoded = html.unescape(raw)
    decoded = re.sub(r'\r\n|\r|\n', '', decoded)
    decoded = re.sub(r'\s+', ' ', decoded).strip()
    return decoded

# ── PARSE XML ────────────────────────────────────────────────────────────────
print("Parsing products.xml...")
tree = ET.parse('products.xml')
root = tree.getroot()
px = root.findall('product')
print(f"  Found {len(px)} products")

products = []
descs = []

for p in px:
    cost = p.findtext('price', '0') or p.findtext('calculated_price', '0') or '0'
    sale_price = markup_price(cost)
    if not sale_price:
        continue

    imgs = []
    for key in ['image', 'image_1', 'image_2', 'image_3', 'image_4', 'image_5']:
        v = (p.findtext(key, '') or '').strip()
        if v:
            imgs.append(v)

    products.append({
        'c': p.findtext('code', '').strip(),
        'n': (p.findtext('name', '') or p.findtext('n', '')).strip(),
        'b': p.findtext('brand', '').strip(),
        'p': sale_price,
        'imgs': imgs,
    })
    descs.append(clean_desc(p.findtext('description', '')))

print(f"  Processed {len(products)} products")

# ── WRITE descs.json ─────────────────────────────────────────────────────────
with open('descs.json', 'w', encoding='utf-8') as f:
    json.dump(descs, f, separators=(',', ':'), ensure_ascii=False)
print(f"  descs.json written ({os.path.getsize('descs.json')//1024}KB)")

# ── BUILD JS CHUNKS ──────────────────────────────────────────────────────────
CHUNK = 400
chunks = [products[i:i+CHUNK] for i in range(0, len(products), CHUNK)]
p_scripts = '\n'.join([f'W.push({json.dumps(c, separators=(",",":"))});' for c in chunks])
brands = sorted(set(p['b'] for p in products if p['b']))
brands_json = json.dumps(brands)
total = len(products)

# ── WRITE index.html ─────────────────────────────────────────────────────────
html_out = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<title>Diecast Catalog</title>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
:root{{--bg:#0d0d0d;--surface:#161616;--card:#1c1c1c;--border:#2a2a2a;--accent:#e8c84a;--text:#f0ede8;--muted:#777;}}
*{{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent;}}
html{{font-size:16px;}}
body{{background:var(--bg);color:var(--text);font-family:"DM Sans",sans-serif;min-height:100vh;overflow-x:hidden;}}
header{{background:var(--surface);border-bottom:2px solid var(--accent);padding:14px 18px;padding-top:max(14px,env(safe-area-inset-top));display:flex;align-items:baseline;gap:12px;position:sticky;top:0;z-index:200;}}
header h1{{font-family:"Bebas Neue",sans-serif;font-size:1.8rem;letter-spacing:4px;color:var(--accent);line-height:1;}}
header span{{font-size:0.68rem;color:var(--muted);letter-spacing:2px;text-transform:uppercase;}}
.controls{{padding:12px 16px;display:flex;flex-direction:column;gap:10px;border-bottom:1px solid var(--border);background:var(--surface);position:sticky;top:58px;z-index:100;}}
.row{{display:flex;gap:8px;}}
.sw{{flex:1;position:relative;}}
.sw::before{{content:"⌕";position:absolute;left:11px;top:50%;transform:translateY(-54%);color:var(--muted);font-size:1.1rem;pointer-events:none;}}
input[type=text]{{width:100%;background:var(--card);border:1px solid var(--border);color:var(--text);padding:11px 12px 11px 34px;border-radius:8px;font-family:"DM Sans",sans-serif;font-size:16px;outline:none;-webkit-appearance:none;}}
input[type=text]:focus{{border-color:var(--accent);}}
select{{flex:1;background:var(--card);border:1px solid var(--border);color:var(--text);padding:11px 28px 11px 10px;border-radius:8px;font-family:"DM Sans",sans-serif;font-size:0.82rem;outline:none;-webkit-appearance:none;appearance:none;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8'%3E%3Cpath d='M1 1l5 5 5-5' stroke='%23777' stroke-width='1.5' fill='none' stroke-linecap='round'/%3E%3C/svg%3E");background-repeat:no-repeat;background-position:right 10px center;}}
.info{{font-size:0.72rem;color:var(--muted);text-align:right;}}
.grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:1px;background:var(--border);}}
@media(min-width:540px){{.grid{{grid-template-columns:repeat(3,1fr);}}}}
@media(min-width:768px){{.grid{{grid-template-columns:repeat(4,1fr);}}}}
@media(min-width:1100px){{.grid{{grid-template-columns:repeat(5,1fr);}}}}
.card{{background:var(--card);display:flex;flex-direction:column;overflow:hidden;cursor:pointer;}}
.card:active{{background:#252525;}}
@media(hover:hover){{.card:hover{{background:#212121;}} .card:hover .iw img{{transform:scale(1.06);}}}}
.iw{{aspect-ratio:4/3;overflow:hidden;background:#111;position:relative;}}
.iw img{{width:100%;height:100%;object-fit:cover;transition:transform .35s ease;display:block;}}
.ni{{width:100%;height:100%;display:flex;align-items:center;justify-content:center;color:#2a2a2a;font-size:2rem;}}
.bt{{position:absolute;top:7px;left:7px;background:rgba(0,0,0,.78);border:1px solid rgba(232,200,74,.35);color:var(--accent);font-size:0.55rem;font-weight:500;letter-spacing:1px;text-transform:uppercase;padding:3px 7px;border-radius:99px;-webkit-backdrop-filter:blur(6px);backdrop-filter:blur(6px);max-width:calc(100% - 14px);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.ic{{position:absolute;bottom:7px;right:7px;background:rgba(0,0,0,.72);color:#ccc;font-size:0.58rem;padding:2px 7px;border-radius:99px;}}
.cb{{padding:10px 11px 12px;flex:1;display:flex;flex-direction:column;gap:7px;}}
.ct{{font-size:0.74rem;font-weight:400;line-height:1.4;color:var(--text);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;}}
.cf{{display:flex;align-items:center;justify-content:space-between;border-top:1px solid var(--border);padding-top:8px;gap:4px;margin-top:auto;}}
.sk{{font-size:0.6rem;color:var(--muted);font-family:"Courier New",monospace;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:55%;}}
.pr{{font-family:"Bebas Neue",sans-serif;font-size:1.1rem;letter-spacing:1px;color:var(--accent);white-space:nowrap;}}
.pagination{{display:flex;justify-content:center;align-items:center;gap:6px;padding:22px 16px;padding-bottom:max(22px,env(safe-area-inset-bottom));border-top:1px solid var(--border);flex-wrap:wrap;}}
.pb{{background:var(--card);border:1px solid var(--border);color:var(--text);min-width:44px;min-height:44px;padding:0 12px;border-radius:8px;cursor:pointer;font-family:"DM Sans",sans-serif;font-size:0.85rem;display:flex;align-items:center;justify-content:center;}}
.pb:active,.pb.on{{background:var(--accent);border-color:var(--accent);color:#000;font-weight:600;}}
.pb:disabled{{opacity:.25;pointer-events:none;}}
.pi{{color:var(--muted);font-size:0.72rem;width:100%;text-align:center;margin-top:4px;}}
.empty{{grid-column:1/-1;padding:60px 20px;text-align:center;color:var(--muted);font-size:.9rem;}}
.mbg{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.93);z-index:500;overflow-y:auto;-webkit-overflow-scrolling:touch;}}
.mbg.open{{display:flex;align-items:flex-start;justify-content:center;}}
.mdl{{background:var(--surface);width:100%;max-width:680px;margin:0 auto;min-height:100%;}}
@media(min-width:700px){{.mdl{{margin:40px auto;min-height:auto;border-radius:12px;overflow:hidden;}}}}
.mhd{{position:sticky;top:0;z-index:10;background:var(--surface);border-bottom:1px solid var(--border);padding:14px 18px;display:flex;align-items:center;justify-content:space-between;}}
.mhd button{{background:var(--card);border:1px solid var(--border);color:var(--text);width:38px;height:38px;border-radius:50%;font-size:1.1rem;cursor:pointer;display:flex;align-items:center;justify-content:center;}}
.msk{{font-family:"Courier New",monospace;font-size:0.72rem;color:var(--muted);}}
.gal{{background:#0a0a0a;}}
.gmain{{width:100%;aspect-ratio:4/3;object-fit:contain;display:block;}}
.gthumbs{{display:flex;gap:6px;padding:10px 14px;overflow-x:auto;-webkit-overflow-scrolling:touch;scrollbar-width:none;background:#111;}}
.gthumbs::-webkit-scrollbar{{display:none;}}
.gthumb{{width:64px;height:48px;object-fit:cover;border-radius:4px;cursor:pointer;border:2px solid transparent;flex-shrink:0;opacity:.55;transition:opacity .2s,border-color .2s;}}
.gthumb.on{{border-color:var(--accent);opacity:1;}}
.mbody{{padding:18px;}}
.mbrand{{display:inline-block;background:rgba(232,200,74,.1);border:1px solid rgba(232,200,74,.3);color:var(--accent);font-size:0.62rem;letter-spacing:1.5px;text-transform:uppercase;padding:4px 10px;border-radius:99px;margin-bottom:12px;}}
.mtitle{{font-size:.95rem;font-weight:400;line-height:1.5;color:var(--text);margin-bottom:14px;}}
.mprice{{font-family:"Bebas Neue",sans-serif;font-size:2rem;letter-spacing:2px;color:var(--accent);margin-bottom:18px;}}
.mdesc{{font-size:0.82rem;line-height:1.65;color:#bbb;border-top:1px solid var(--border);padding-top:16px;}}
.mdesc ul{{padding-left:18px;}}
.mdesc li{{margin-bottom:5px;}}
.dload{{color:var(--muted);font-size:0.8rem;font-style:italic;}}
#loader{{position:fixed;inset:0;background:var(--bg);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:20px;z-index:999;font-family:"Bebas Neue",sans-serif;font-size:1.4rem;letter-spacing:3px;color:var(--accent);}}
.spin{{width:40px;height:40px;border:3px solid var(--border);border-top-color:var(--accent);border-radius:50%;animation:spin .7s linear infinite;}}
@keyframes spin{{to{{transform:rotate(360deg);}}}}
</style>
</head>
<body>
<div id="loader"><div class="spin"></div>LOADING CATALOG</div>
<header><h1>Diecast Catalog</h1><span id="tb">— Models</span></header>
<div class="controls">
  <div class="sw"><input type="text" id="q" placeholder="Search name, brand, SKU…" oninput="onF()" autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false"></div>
  <div class="row">
    <select id="bs" onchange="onF()"><option value="">All Brands</option></select>
    <select id="ss" onchange="onF()">
      <option value="name">Name A–Z</option>
      <option value="pa">Price ↑</option>
      <option value="pd">Price ↓</option>
      <option value="sku">SKU</option>
    </select>
  </div>
  <div class="info" id="inf"></div>
</div>
<div class="grid" id="grid"></div>
<div class="pagination" id="pg"></div>
<div class="mbg" id="mbg" onclick="bgClick(event)">
  <div class="mdl">
    <div class="mhd"><span class="msk" id="msk"></span><button onclick="closeM()">✕</button></div>
    <div class="gal"><img class="gmain" id="gmain" src="" alt=""><div class="gthumbs" id="gthumbs"></div></div>
    <div class="mbody">
      <div class="mbrand" id="mbrand"></div>
      <div class="mtitle" id="mtitle"></div>
      <div class="mprice" id="mprice"></div>
      <div class="mdesc" id="mdesc"><span class="dload">Tap a product to see description</span></div>
    </div>
  </div>
</div>
<script>
const W=[];
{p_scripts}
const PRODUCTS=W.flat();
const PS=40;
let fil=[],pg=1,DESCS=null,descLoading=false,pendingIdx=null;
function e(s){{return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}}
function onF(){{pg=1;aF();}}
function aF(){{
  const q=document.getElementById('q').value.toLowerCase();
  const br=document.getElementById('bs').value;
  const so=document.getElementById('ss').value;
  fil=PRODUCTS.filter(p=>(!q||p.n.toLowerCase().includes(q)||p.b.toLowerCase().includes(q)||p.c.toLowerCase().includes(q))&&(!br||p.b===br));
  fil.sort((a,b)=>so==='pa'?+a.p-+b.p:so==='pd'?+b.p-+a.p:so==='sku'?a.c.localeCompare(b.c):a.n.localeCompare(b.n));
  document.getElementById('inf').textContent=fil.length.toLocaleString()+' products found';
  rG();rP();
}}
function rG(){{
  const g=document.getElementById('grid');
  const sl=fil.slice((pg-1)*PS,pg*PS);
  if(!sl.length){{g.innerHTML='<div class="empty">No products found.</div>';return;}}
  g.innerHTML=sl.map((p,i)=>{{
    const idx=(pg-1)*PS+i;
    const ps=p.p?'$'+p.p:'—';
    const img=p.imgs&&p.imgs.length?p.imgs[0]:'';
    const ih=img?`<img src="${{e(img)}}" alt="" loading="lazy" onerror="this.parentElement.innerHTML='<div class=\\"ni\\">🚗</div>'">`:'<div class="ni">🚗</div>';
    const ic=p.imgs&&p.imgs.length>1?`<span class="ic">📷 ${{p.imgs.length}}</span>`:'';
    return `<div class="card" onclick="openM(${{idx}})"><div class="iw">${{ih}}<span class="bt">${{e(p.b)}}</span>${{ic}}</div><div class="cb"><div class="ct">${{e(p.n)}}</div><div class="cf"><span class="sk">${{e(p.c)}}</span><span class="pr">${{ps}}</span></div></div></div>`;
  }}).join('');
}}
function rP(){{
  const tot=Math.ceil(fil.length/PS);
  const el=document.getElementById('pg');
  if(tot<=1){{el.innerHTML='';return;}}
  const rng=new Set([1,tot]);
  for(let i=Math.max(2,pg-2);i<=Math.min(tot-1,pg+2);i++)rng.add(i);
  const arr=[...rng].sort((a,b)=>a-b);
  let h=`<button class="pb" onclick="gP(${{pg-1}})" ${{pg===1?'disabled':''}}>←</button>`;
  let last=0;
  for(const n of arr){{
    if(n-last>1)h+=`<span style="color:var(--muted)">…</span>`;
    h+=`<button class="pb ${{n===pg?'on':''}}" onclick="gP(${{n}})">${{n}}</button>`;
    last=n;
  }}
  h+=`<button class="pb" onclick="gP(${{pg+1}})" ${{pg===tot?'disabled':''}}>→</button>`;
  h+=`<div class="pi">Page ${{pg}} of ${{tot}}</div>`;
  el.innerHTML=h;
}}
function gP(n){{
  const tot=Math.ceil(fil.length/PS);
  if(n<1||n>tot)return;
  pg=n;rG();rP();
  window.scrollTo({{top:0,behavior:'smooth'}});
}}
function openM(idx){{
  const p=fil[idx];if(!p)return;
  pendingIdx=PRODUCTS.indexOf(p);
  document.getElementById('msk').textContent='SKU: '+p.c;
  document.getElementById('mbrand').textContent=p.b;
  document.getElementById('mtitle').textContent=p.n;
  document.getElementById('mprice').textContent=p.p?'$'+p.p:'—';
  document.getElementById('mdesc').innerHTML='<span class="dload">Loading description…</span>';
  const imgs=p.imgs||[];
  const gm=document.getElementById('gmain');
  const gt=document.getElementById('gthumbs');
  if(imgs.length>0){{
    gm.src=imgs[0];gm.style.display='block';
    if(imgs.length>1){{gt.style.display='flex';gt.innerHTML=imgs.map((s,i)=>`<img class="gthumb ${{i===0?'on':''}}" src="${{e(s)}}" onclick="setImg(this,'${{e(s)}}')" loading="lazy">`).join('');}}
    else{{gt.style.display='none';gt.innerHTML='';}}
  }}else{{gm.style.display='none';gt.style.display='none';}}
  document.getElementById('mbg').classList.add('open');
  document.body.style.overflow='hidden';
  loadDescs();
}}
function loadDescs(){{
  if(DESCS){{showDesc();return;}}
  if(descLoading)return;
  descLoading=true;
  fetch('descs.json').then(r=>r.json()).then(d=>{{DESCS=d;showDesc();}}).catch(()=>{{document.getElementById('mdesc').innerHTML='<span class="dload">Description unavailable.</span>';}});
}}
function showDesc(){{
  if(pendingIdx===null||!DESCS)return;
  const d=DESCS[pendingIdx]||'';
  document.getElementById('mdesc').innerHTML=d?`<div>${{d}}</div>`:'<span class="dload">No description available.</span>';
}}
function setImg(el,src){{document.getElementById('gmain').src=src;document.querySelectorAll('.gthumb').forEach(t=>t.classList.remove('on'));el.classList.add('on');}}
function closeM(){{document.getElementById('mbg').classList.remove('open');document.body.style.overflow='';}}
function bgClick(e){{if(e.target===document.getElementById('mbg'))closeM();}}
document.addEventListener('keydown',e=>{{if(e.key==='Escape')closeM();}});
setTimeout(()=>{{
  document.getElementById('tb').textContent=PRODUCTS.length.toLocaleString()+' Models';
  const brands={brands_json};
  const sel=document.getElementById('bs');
  brands.forEach(b=>{{const o=document.createElement('option');o.value=b;o.textContent=b;sel.appendChild(o);}});
  fil=[...PRODUCTS];aF();
  document.getElementById('loader').style.display='none';
}},50);
</script>
</body>
</html>'''

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html_out)

print(f"Built index.html ({os.path.getsize('index.html')//1024}KB) — {total} products, {len(brands)} brands")
