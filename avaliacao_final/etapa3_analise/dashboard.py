#!/usr/bin/env python3
"""
Avaliação Final — Etapa 3 · Gera dashboard.html (Plotly.js embutido, abre offline, sem servidor)

Lê SOMENTE a Gold layer (bigdata_aval/gold/*.parquet). Todas as taxas são recalculadas no
navegador a partir das contagens, por isso respondem aos filtros sem distorção.
Uso: python3 avaliacao_final/etapa3_analise/dashboard.py
"""
import json
import os
from pathlib import Path

import duckdb
import plotly

BASE = Path(os.environ.get("BIGDATA_DIR", "bigdata_aval"))
AQUI = Path(__file__).resolve().parent
PLOTLY_JS = (Path(plotly.__file__).parent / "package_data" / "plotly.min.js").read_text(encoding="utf-8")

con = duckdb.connect()
g = lambda t: f"read_parquet('{BASE / 'gold' / (t + '.parquet')}')"

cubo = con.sql(f"""
SELECT month AS m, channel AS c, merchant_category AS k, segment AS s, periodo_dia AS p,
       transacoes::INT AS n, fraudes::INT AS f, recusadas::INT AS r, recusas_legitimas::INT AS rl,
       valor_total AS v, valor_fraude AS vf
FROM {g('gold_cubo_risco')} ORDER BY ALL""").df()
horario = con.sql(f"""
SELECT hora AS h, dia_semana_num AS d, transacoes::INT AS n, fraudes::INT AS f
FROM {g('gold_perfil_horario')} ORDER BY ALL""").df()
diaria = con.sql(f"""
SELECT strftime(data, '%Y-%m-%d') AS dt, channel AS c, transacoes::INT AS n, fraudes::INT AS f
FROM {g('gold_serie_diaria')} ORDER BY ALL""").df()
motor = con.sql(f"""
SELECT SUM(transacoes)::INT AS n, SUM(fraudes)::INT AS f
FROM {g('gold_segmento_score')} WHERE faixa_risk_score LIKE '3_%'""").fetchone()

dados = {
    "cubo": cubo.to_dict(orient="list"),
    "horario": horario.to_dict(orient="list"),
    "diaria": diaria.to_dict(orient="list"),
    "motor": {"n": motor[0], "f": motor[1]},
}

HTML = r"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TechPay — Painel de risco de fraude 2025</title>
<style>
:root{
  --navy:#0B2E59; --navy-2:#1F4E8C; --navy-soft:#E7EDF5;
  --gold:#B8860B; --gold-soft:#F6EFD9;
  --green:#1E5631; --green-soft:#E3EFE6;
  --ink:#16212E; --ink-2:#4A5767; --ink-3:#7A8697;
  --rule:#D9DFE7; --paper:#FFFFFF; --bg:#F5F7FA;
  --num:"Bahnschrift","DIN Alternate","Roboto Condensed","Segoe UI",system-ui,sans-serif;
  --txt:"Segoe UI",system-ui,-apple-system,"Helvetica Neue",Arial,sans-serif;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 var(--txt)}
header{background:var(--navy);color:#fff;padding:22px 32px 18px}
.titulo{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 18px}
h1{font:600 26px/1.15 var(--num);letter-spacing:.2px;margin:0}
.sub{color:#C9D6E8;font-size:14px}
.filtros{display:flex;flex-wrap:wrap;gap:12px 18px;margin-top:16px;align-items:flex-end}
.filtros label{display:flex;flex-direction:column;font-size:12.5px;color:#C9D6E8;gap:4px}
.filtros select{font:14px var(--txt);min-width:150px;padding:6px 8px;border:1px solid #3A5F8F;border-radius:4px;background:#fff;color:var(--ink)}
.filtros button{font:600 13.5px var(--txt);padding:7px 14px;border-radius:4px;border:1px solid var(--gold);background:transparent;color:#F3E3B5;cursor:pointer}
.filtros button:hover{background:rgba(184,134,11,.18)}
:focus-visible{outline:3px solid var(--gold);outline-offset:2px}
.ativo{font-size:13px;color:#F3E3B5;min-height:18px;margin-top:10px}
main{max-width:1320px;margin:0 auto;padding:0 24px 40px}

.kpis{display:grid;grid-template-columns:repeat(4,1fr);background:var(--paper);border-bottom:1px solid var(--rule)}
.kpi{padding:18px 24px 16px;border-left:1px solid var(--rule)}
.kpi:first-child{border-left:0}
.kpi .rot{font-size:13px;color:var(--ink-2)}
.kpi .val{font:600 34px/1.1 var(--num);color:var(--navy);margin:4px 0 2px;font-variant-numeric:tabular-nums}
.kpi .ctx{font-size:12.5px;color:var(--ink-3)}
.kpi .ctx b{font-weight:600}
.acima{color:var(--gold)} .abaixo{color:var(--green)}

section{background:var(--paper);margin-top:18px;padding:18px 22px 10px;border-top:3px solid var(--navy)}
section.destaque{border-top-color:var(--gold)}
h2{font:600 18px/1.25 var(--num);margin:0 0 2px;color:var(--navy)}
.nota{font-size:12.5px;color:var(--ink-3);margin:0 0 6px;max-width:78ch}
.grade{display:grid;gap:18px}
.g2{grid-template-columns:1.25fr 1fr}
.g2b{grid-template-columns:1fr 1fr}
.graf{width:100%;height:330px}
.graf.alto{height:380px}

.decisao{display:grid;grid-template-columns:minmax(260px,0.62fr) 1.9fr;gap:22px;align-items:start}
.controles{display:flex;gap:16px;align-items:center;flex-wrap:wrap;font-size:13.5px;color:var(--ink-2);margin:6px 0 8px}
.controles input[type=range]{accent-color:var(--navy);width:220px}
.leitura{font:600 15px/1.4 var(--num);color:var(--ink);background:var(--gold-soft);border-left:4px solid var(--gold);padding:8px 12px;margin:4px 0 10px}
.tabwrap{overflow:auto;max-height:430px;border:1px solid var(--rule)}
table{border-collapse:collapse;width:100%;font-size:12.5px;font-variant-numeric:tabular-nums}
th{position:sticky;top:0;background:var(--navy);color:#fff;font-weight:600;text-align:right;padding:7px 6px;cursor:pointer;white-space:normal;vertical-align:bottom;line-height:1.2}
th.t{text-align:left}
td{padding:5px 6px;border-bottom:1px solid #EDF0F4;text-align:right;white-space:nowrap}
td.t{text-align:left}
tr.corte td{background:var(--gold-soft)}
tr.corte + tr:not(.corte) td{border-top:2px solid var(--gold)}
.barra{display:inline-block;height:9px;background:var(--navy-2);vertical-align:middle;margin-right:6px}
footer{max-width:1320px;margin:18px auto 0;padding:0 24px;font-size:12px;color:var(--ink-3)}
@media (max-width:980px){
  .kpis{grid-template-columns:repeat(2,1fr)}
  .kpi:nth-child(3){border-left:0}
  .g2,.g2b,.decisao{grid-template-columns:1fr}
  header{padding:18px}
  main{padding:0 12px 30px}
}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
</style>
</head>
<body>
<header>
  <div class="titulo">
    <h1>TechPay — risco de fraude em transações</h1>
    <span class="sub">Base da avaliação, 01/01/2025 a 31/12/2025, fonte: Gold layer do pipeline</span>
  </div>
  <div class="filtros" role="group" aria-label="Filtros">
    <label>Canal<select id="fc"></select></label>
    <label>Categoria do estabelecimento<select id="fk"></select></label>
    <label>Segmento<select id="fs"></select></label>
    <label>Período do dia<select id="fp"></select></label>
    <label>Mês<select id="fm"></select></label>
    <button id="limpar" type="button">Limpar filtros</button>
  </div>
  <div class="ativo" id="ativo" aria-live="polite"></div>
</header>

<main>
  <div class="kpis" id="kpis" aria-live="polite"></div>

  <section>
    <div class="grade g2">
      <div>
        <h2>Tendência mensal</h2>
        <p class="nota">Barras: transações no mês. Linha: taxa de fraude (fraudes ÷ transações). Tracejado: taxa geral da base.</p>
        <div id="gTend" class="graf"></div>
      </div>
      <div>
        <h2>Média móvel de 7 dias da taxa de fraude</h2>
        <p class="nota">Série diária da tabela gold_serie_diaria. Responde apenas ao filtro de canal.</p>
        <div id="gDia" class="graf"></div>
      </div>
    </div>
  </section>

  <section>
    <div class="grade g2b">
      <div>
        <h2>Taxa de fraude por canal</h2>
        <p class="nota">Amarelo: acima da taxa geral. Verde: abaixo. Rótulo: fraudes / transações.</p>
        <div id="gCanal" class="graf"></div>
      </div>
      <div>
        <h2>Taxa de fraude por categoria de estabelecimento</h2>
        <p class="nota">Mesma leitura de cores do gráfico ao lado.</p>
        <div id="gCat" class="graf"></div>
      </div>
      <div>
        <h2>Taxa de fraude por segmento</h2>
        <p class="nota">Passe o mouse para ver a participação de cada segmento no volume e nas fraudes.</p>
        <div id="gSeg" class="graf"></div>
      </div>
      <div>
        <h2>Canal × categoria</h2>
        <p class="nota">Cada célula: taxa de fraude da combinação. Passe o mouse para ver volume e fraudes.</p>
        <div id="gMapa" class="graf"></div>
      </div>
    </div>
  </section>

  <section>
    <h2>Hora do dia × dia da semana</h2>
    <p class="nota">Taxa de fraude por hora e dia (tabela gold_perfil_horario, visão da base inteira, não responde aos filtros).</p>
    <div id="gHora" class="graf alto"></div>
  </section>

  <section class="destaque">
    <h2>Onde aplicar autenticação extra</h2>
    <p class="nota">Combinações de canal, categoria, segmento e período ordenadas da maior para a menor taxa de fraude.
      Combinações com poucas transações são reunidas num grupo mais amplo ("Demais" indica a dimensão agrupada). A curva mostra quanto das fraudes do recorte seria alcançado ao exigir autenticação extra nas combinações do topo,
      e quanto do volume seria afetado. Números calculados sobre a própria base de 2025, sem validação fora da amostra; quanto menor o agrupamento mínimo, mais otimista fica a curva.</p>
    <div class="controles">
      <label for="corte">Volume submetido à autenticação extra:</label>
      <input type="range" id="corte" min="1" max="60" value="20" step="1">
      <span id="corteVal"></span>
      <label>Reunir combinações com menos de
        <select id="minN"><option value="1">1 (não reunir)</option><option>30</option><option selected>50</option><option>100</option></select> transações
      </label>
    </div>
    <div class="leitura" id="leitura"></div>
    <div class="decisao">
      <div id="gCurva" class="graf alto"></div>
      <div class="tabwrap"><table id="tab"><thead></thead><tbody></tbody></table></div>
    </div>
  </section>
</main>
<footer>Gerado por avaliacao_final/etapa3_analise/dashboard.py a partir de bigdata_aval/gold/. Rota sem admin: DuckDB + Plotly.</footer>

<script>__PLOTLY__</script>
<script>
const D = __DADOS__;
const NOMES = {
  c:{app:"App",web:"Web",pos:"POS",atm:"ATM"},
  k:{varejo:"Varejo",viagem:"Viagem",eletronico:"Eletrônico",alimentacao:"Alimentação",servicos:"Serviços",saude:"Saúde"},
  s:{"Premium":"Premium","Standard":"Standard","High-Risk":"High-Risk"},
  p:{madrugada:"Madrugada (0h–5h)",manha:"Manhã (6h–11h)",tarde:"Tarde (12h–17h)",noite:"Noite (18h–23h)"},
  m:{1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"}
};
const DIAS = ["Seg","Ter","Qua","Qui","Sex","Sáb","Dom"];
const COR = {navy:"#0B2E59", navy2:"#1F4E8C", gold:"#B8860B", green:"#1E5631", ink:"#16212E", ink3:"#7A8697", rule:"#D9DFE7"};
const nf0 = new Intl.NumberFormat("pt-BR",{maximumFractionDigits:0});
const nf1 = new Intl.NumberFormat("pt-BR",{minimumFractionDigits:1,maximumFractionDigits:1});
const nf2 = new Intl.NumberFormat("pt-BR",{minimumFractionDigits:2,maximumFractionDigits:2});
const brl = v => "R$ " + nf0.format(v);
const pct = (a,b,f=nf2) => b ? f.format(100*a/b) + "%" : "–";
const FONT = {family:'"Segoe UI",system-ui,sans-serif', size:12.5, color:COR.ink};
const CFG = {displayModeBar:false, responsive:true, locale:"pt-BR"};
// Plotly grava estado (ex.: tipo do eixo) dentro do objeto de layout recebido,
// então cada gráfico recebe um layout novo, nunca um objeto compartilhado.
function L(extra){
  const ax = o => ({gridcolor:COR.rule, zeroline:false, ...(o||{})});
  const {xaxis, yaxis, ...resto} = extra || {};
  return {font:{...FONT}, paper_bgcolor:"#fff", plot_bgcolor:"#fff", margin:{l:56,r:20,t:14,b:44},
          separators:",.", hoverlabel:{font:{family:FONT.family}}, xaxis:ax(xaxis), yaxis:ax(yaxis), ...resto};
}

// linhas do cubo como objetos
const C = D.cubo; const LINHAS = C.m.map((_,i)=>({m:C.m[i],c:C.c[i],k:C.k[i],s:C.s[i],p:C.p[i],n:C.n[i],f:C.f[i],r:C.r[i],rl:C.rl[i],v:C.v[i],vf:C.vf[i]}));
const TOT = soma(LINHAS); const TAXA_GERAL = TOT.f/TOT.n;

function soma(rows){ const o={n:0,f:0,r:0,rl:0,v:0,vf:0}; for(const x of rows){o.n+=x.n;o.f+=x.f;o.r+=x.r;o.rl+=x.rl;o.v+=x.v;o.vf+=x.vf;} return o; }
function agrupa(rows, chaves){ const mp=new Map(); for(const x of rows){ const id=chaves.map(k=>x[k]).join("|"); if(!mp.has(id)) mp.set(id,{chave:Object.fromEntries(chaves.map(k=>[k,x[k]])),rows:[]}); mp.get(id).rows.push(x);} return [...mp.values()].map(g=>({...g.chave,...soma(g.rows)})); }

// filtros
const F = {c:"fc",k:"fk",s:"fs",p:"fp",m:"fm"};
for(const [dim,id] of Object.entries(F)){
  const sel=document.getElementById(id);
  sel.add(new Option("Todos",""));
  for(const [val,nome] of Object.entries(NOMES[dim])) sel.add(new Option(nome,val));
  sel.addEventListener("change",render);
}
document.getElementById("limpar").addEventListener("click",()=>{ for(const id of Object.values(F)) document.getElementById(id).value=""; render(); });
document.getElementById("corte").addEventListener("input",renderDecisao);
document.getElementById("minN").addEventListener("change",renderDecisao);
function filtroAtual(){ const o={}; for(const [dim,id] of Object.entries(F)){ const v=document.getElementById(id).value; if(v!=="") o[dim]= dim==="m" ? +v : v; } return o; }
function aplica(rows, fil, ignora=[]){ return rows.filter(x=>Object.entries(fil).every(([d,v])=>ignora.includes(d)||x[d]===v)); }

function render(){
  const fil=filtroAtual(); const rows=aplica(LINHAS,fil); const t=soma(rows);
  const desc=Object.entries(fil).map(([d,v])=>NOMES[d][v]).join(", ");
  document.getElementById("ativo").textContent = desc ? "Recorte: " + desc + " (" + nf0.format(t.n) + " transações)" : "Sem filtros: base completa";
  renderKpis(t, fil); renderTend(fil); renderDia(fil); renderComp(fil); renderMapa(fil); renderDecisao();
}

function renderKpis(t, fil){
  const taxa=t.n? t.f/t.n : 0; const dif = taxa/TAXA_GERAL;
  const cls = taxa>TAXA_GERAL*1.05 ? "acima" : (taxa<TAXA_GERAL*0.95 ? "abaixo":"");
  const temFiltro = Object.keys(fil).length>0;
  const legit = t.n - t.f;
  document.getElementById("kpis").innerHTML = `
   <div class="kpi"><div class="rot">Transações</div><div class="val">${nf0.format(t.n)}</div>
     <div class="ctx">${temFiltro? pct(t.n,TOT.n,nf1)+" do volume total" : "valor total "+brl(t.v)}</div></div>
   <div class="kpi"><div class="rot">Taxa de fraude</div><div class="val ${cls}">${pct(t.f,t.n)}</div>
     <div class="ctx">${nf0.format(t.f)} fraudes${temFiltro? `, <b class="${cls}">${nf2.format(dif)}×</b> a taxa geral de ${pct(TOT.f,TOT.n)}`:""}</div></div>
   <div class="kpi"><div class="rot">Valor fraudado</div><div class="val">${brl(t.vf)}</div>
     <div class="ctx">${pct(t.vf,t.v)} do valor transacionado — ticket médio da fraude ${t.f? brl(t.vf/t.f):"–"}</div></div>
   <div class="kpi"><div class="rot">Clientes legítimos recusados</div><div class="val">${nf0.format(t.rl)}</div>
     <div class="ctx">${pct(t.rl,t.r,nf1)} das ${nf0.format(t.r)} recusas; ${pct(t.rl,legit)} das transações legítimas</div></div>`;
}

function renderTend(fil){
  const g=agrupa(aplica(LINHAS,fil,["m"]),["m"]).sort((a,b)=>a.m-b.m);
  const x=g.map(r=>NOMES.m[r.m]);
  Plotly.react("gTend",[
    {type:"bar",x,y:g.map(r=>r.n),name:"Transações",marker:{color:"#C9D6E8"},
     hovertemplate:"%{x}: %{y:,.0f} transações<extra></extra>"},
    {type:"scatter",mode:"lines+markers",x,y:g.map(r=>100*r.f/r.n),name:"Taxa de fraude",yaxis:"y2",
     line:{color:COR.navy,width:3},marker:{size:7},customdata:g.map(r=>r.f),
     hovertemplate:"%{x}: %{y:.2f}% (%{customdata} fraudes)<extra></extra>"},
    {type:"scatter",mode:"lines",x,y:x.map(()=>100*TAXA_GERAL),name:"Taxa geral",yaxis:"y2",line:{color:COR.gold,dash:"dash",width:1.5},hoverinfo:"skip"}
  ],L({showlegend:true, legend:{orientation:"h",y:1.12,x:0}, margin:{l:56,r:64,t:14,b:44},
     xaxis:{type:"category"},
     yaxis:{side:"right",showgrid:false,title:"Transações",rangemode:"tozero",tickformat:",.0f"},
     yaxis2:{overlaying:"y",side:"left",gridcolor:COR.rule,title:"Taxa de fraude (%)",rangemode:"tozero",ticksuffix:"%",tickformat:".1f",tickmode:"auto",nticks:6,zeroline:false}}), CFG);
}

function renderDia(fil){
  const Dd=D.diaria; const porDia=new Map();
  for(let i=0;i<Dd.dt.length;i++){ if(fil.c && Dd.c[i]!==fil.c) continue; const o=porDia.get(Dd.dt[i])||{n:0,f:0}; o.n+=Dd.n[i]; o.f+=Dd.f[i]; porDia.set(Dd.dt[i],o); }
  const dias=[...porDia.keys()].sort(); const mm=[];
  for(let i=0;i<dias.length;i++){ if(i<6){mm.push(null);continue;} let n=0,f=0; for(let j=i-6;j<=i;j++){const o=porDia.get(dias[j]); n+=o.n; f+=o.f;} mm.push(100*f/n); }
  Plotly.react("gDia",[
    {type:"scatter",mode:"lines",x:dias,y:mm,line:{color:COR.navy2,width:1.6},name:"Média móvel 7 dias",
     hovertemplate:"%{x|%d/%m}: %{y:.2f}%<extra></extra>"},
    {type:"scatter",mode:"lines",x:[dias[0],dias[dias.length-1]],y:[100*TAXA_GERAL,100*TAXA_GERAL],line:{color:COR.gold,dash:"dash",width:1.5},hoverinfo:"skip",name:"Taxa geral"}
  ],L({showlegend:false, xaxis:{type:"date",showgrid:false,tickvals:Object.keys(NOMES.m).map(m=>`2025-${String(m).padStart(2,"0")}-01`),ticktext:Object.values(NOMES.m)},
     yaxis:{title:"Taxa de fraude (%)",ticksuffix:"%",rangemode:"tozero"}}), CFG);
}

function barras(div, dim, fil){
  const g=agrupa(aplica(LINHAS,fil,[dim]),[dim]).map(r=>({...r,t:r.n?100*r.f/r.n:0})).sort((a,b)=>a.t-b.t);
  Plotly.react(div,[{type:"bar",orientation:"h",y:g.map(r=>NOMES[dim][r[dim]]),x:g.map(r=>r.t),
    marker:{color:g.map(r=>r.t>100*TAXA_GERAL*1.05?COR.gold:(r.t<100*TAXA_GERAL*0.95?COR.green:COR.navy2))},
    text:g.map(r=>`${nf2.format(r.t)}%   ${r.f} / ${nf0.format(r.n)}`),textposition:"outside",cliponaxis:false,
    customdata:g.map(r=>[pct(r.n,g.reduce((a,b)=>a+b.n,0),nf1),pct(r.f,g.reduce((a,b)=>a+b.f,0),nf1),brl(r.vf)]),
    hovertemplate:"%{y}<br>Taxa: %{x:.2f}%<br>%{customdata[0]} do volume, %{customdata[1]} das fraudes<br>Valor fraudado: %{customdata[2]}<extra></extra>"}],
   L({margin:{l:130,r:130,t:10,b:44},
    xaxis:{type:"linear",title:"Taxa de fraude (%)",ticksuffix:"%",rangemode:"tozero"}, yaxis:{type:"category",ticklabelstandoff:10,showgrid:false},
    shapes:[{type:"line",x0:100*TAXA_GERAL,x1:100*TAXA_GERAL,yref:"paper",y0:0,y1:1,line:{color:COR.gold,dash:"dash",width:1.5}}]}), CFG);
}
function renderComp(fil){ barras("gCanal","c",fil); barras("gCat","k",fil); barras("gSeg","s",fil); }

function renderMapa(fil){
  const rows=aplica(LINHAS,fil,["c","k"]);
  const cs=["app","web","pos","atm"], ks=["viagem","saude","alimentacao","varejo","servicos","eletronico"];
  const z=[],txt=[],cd=[];
  for(const c of cs){ const lz=[],lt=[],lc=[]; for(const k of ks){ const t=soma(rows.filter(x=>x.c===c&&x.k===k)); const v=t.n?100*t.f/t.n:null; lz.push(v); lt.push(v===null?"":nf1.format(v)+"%"); lc.push([t.f,nf0.format(t.n)]);} z.push(lz);txt.push(lt);cd.push(lc);}
  Plotly.react("gMapa",[{type:"heatmap",x:ks.map(k=>NOMES.k[k]),y:cs.map(c=>NOMES.c[c]),z,text:txt,texttemplate:"%{text}",customdata:cd,
    colorscale:[[0,"#FFFFFF"],[0.5,"#7FA0C8"],[1,COR.navy]],zmin:0,
    hovertemplate:"%{y} × %{x}<br>Taxa: %{z:.2f}%<br>%{customdata[0]} fraudes em %{customdata[1]} transações<extra></extra>",
    colorbar:{ticksuffix:"%",thickness:12}}],
   L({margin:{l:50,r:10,t:10,b:60}, xaxis:{type:"category",showgrid:false}, yaxis:{type:"category",autorange:"reversed",showgrid:false}}), CFG);
}

function renderHora(){
  const H=D.horario; const z=Array.from({length:7},()=>Array(24).fill(null)), cd=Array.from({length:7},()=>Array(24).fill(null));
  for(let i=0;i<H.h.length;i++){ z[H.d[i]-1][H.h[i]]=100*H.f[i]/H.n[i]; cd[H.d[i]-1][H.h[i]]=[H.f[i],H.n[i]]; }
  const tot=Array(24).fill(0).map((_,h)=>{let n=0,f=0; for(let i=0;i<H.h.length;i++) if(H.h[i]===h){n+=H.n[i];f+=H.f[i];} return 100*f/n;});
  Plotly.newPlot("gHora",[
    {type:"heatmap",x:[...Array(24).keys()].map(h=>h+"h"),y:DIAS,z,customdata:cd,colorscale:[[0,"#FFFFFF"],[0.5,"#7FA0C8"],[1,COR.navy]],zmin:0,
     hovertemplate:"%{y}, %{x}<br>Taxa: %{z:.2f}%<br>%{customdata[0]} fraudes em %{customdata[1]} transações<extra></extra>",
     colorbar:{ticksuffix:"%",thickness:12,len:0.62,y:0.69}},
    {type:"bar",x:[...Array(24).keys()].map(h=>h+"h"),y:tot,xaxis:"x",yaxis:"y2",
     marker:{color:tot.map(v=>v>100*TAXA_GERAL*1.05?COR.gold:(v<100*TAXA_GERAL*0.95?COR.green:COR.navy2))},
     hovertemplate:"%{x}, todos os dias: %{y:.2f}%<extra></extra>"}
  ],L({margin:{l:70,r:20,t:10,b:40}, showlegend:false,
     yaxis:{type:"category",domain:[0.38,1],autorange:"reversed",showgrid:false}, yaxis2:{domain:[0,0.3],ticksuffix:"%",title:"Todos os dias",gridcolor:COR.rule,zeroline:false},
     xaxis:{type:"category",anchor:"y2",showgrid:false},
     shapes:[{type:"line",xref:"paper",x0:0,x1:1,yref:"y2",y0:100*TAXA_GERAL,y1:100*TAXA_GERAL,line:{color:COR.gold,dash:"dash",width:1.5}}]}), CFG);
}

let ordemTab={col:"t",dir:-1};
function renderDecisao(){
  const fil=filtroAtual(); const rows=aplica(LINHAS,fil); const t=soma(rows);
  const minN=+document.getElementById("minN").value;
  const corte=+document.getElementById("corte").value;
  document.getElementById("corteVal").textContent = corte + "% das transações do recorte";
  // agrupamento em níveis: célula pequena (menos de minN transações) sobe para um grupo mais amplo
  // canal+categoria+segmento+período → canal+categoria+segmento → canal+segmento → segmento → resto.
  // Assim toda linha continua sendo uma regra aplicável e nenhuma fraude fica fora da ordenação.
  const NIVEIS=[["c","k","s","p"],["c","k","s"],["c","s"],["s"]];
  const combos=[]; let pendentes=rows;
  for(const chaves of NIVEIS){
    const grupos=new Map();
    for(const x of pendentes){ const id=chaves.map(k=>x[k]).join("|"); if(!grupos.has(id)) grupos.set(id,[]); grupos.get(id).push(x); }
    pendentes=[];
    for(const [id,rs] of grupos){
      const tt=soma(rs);
      if(tt.n>=minN) combos.push({...Object.fromEntries(chaves.map(k=>[k,rs[0][k]])),...tt,id:chaves.length+":"+id,nivel:chaves.length});
      else pendentes.push(...rs);
    }
  }
  if(pendentes.length) combos.push({...soma(pendentes),id:"_resto",resto:true});
  combos.forEach(r=>r.t=r.n?r.f/r.n:0);
  // a linha "resto" (se existir) não é uma regra aplicável: fica sempre por último
  combos.sort((a,b)=>(!!a.resto-!!b.resto)||b.t-a.t||b.n-a.n);
  // curva de captura (todas as combinações)
  const cx=[0],cy=[0]; let an=0,af=0;
  combos.forEach(r=>{an+=r.n;af+=r.f;r.an=an;r.af=af;cx.push(100*an/t.n);cy.push(t.f?100*af/t.f:0);});
  // ponto de corte
  let sel=combos.filter(r=>100*(r.an-r.n)/t.n < corte);
  const sn=sel.reduce((a,b)=>a+b.n,0), sf=sel.reduce((a,b)=>a+b.f,0);
  document.getElementById("leitura").textContent = t.f
    ? `Autenticação extra nos ${sel.length} grupos do topo: ${nf0.format(sn)} transações (${pct(sn,t.n,nf1)} do recorte) alcançam ${nf0.format(sf)} fraudes (${pct(sf,t.f,nf1)} do recorte). Taxa de fraude dentro do grupo: ${pct(sf,sn)}; ${nf0.format(sn-sf)} transações legítimas passariam pela etapa extra.`
    : "Não há fraudes neste recorte.";
  const semFiltro=Object.keys(fil).length===0;
  const tr=[
    {type:"scatter",mode:"lines",x:cx,y:cy,name:"Combinações ordenadas por taxa",line:{color:COR.navy,width:3},
     hovertemplate:"%{x:.1f}% do volume → %{y:.1f}% das fraudes<extra></extra>"},
    {type:"scatter",mode:"lines",x:[0,100],y:[0,100],name:"Seleção sem critério",line:{color:COR.ink3,dash:"dot",width:1.2},hoverinfo:"skip"},
    {type:"scatter",mode:"markers",x:[100*sn/t.n],y:[t.f?100*sf/t.f:0],name:"Corte escolhido",marker:{color:COR.gold,size:13,line:{color:"#fff",width:2}},
     hovertemplate:"Corte: %{x:.1f}% do volume → %{y:.1f}% das fraudes<extra></extra>"}];
  if(semFiltro) tr.push({type:"scatter",mode:"markers",x:[100*D.motor.n/TOT.n],y:[100*D.motor.f/TOT.f],name:"Motor atual (risk_score ≥ 80)",
     marker:{color:COR.green,size:12,symbol:"diamond",line:{color:"#fff",width:1.5}},hovertemplate:"risk_score ≥ 80: %{x:.1f}% do volume → %{y:.1f}% das fraudes<extra></extra>"});
  Plotly.react("gCurva",tr,L({legend:{orientation:"h",y:-0.22,x:0}, margin:{l:56,r:16,t:10,b:100},
     xaxis:{type:"linear",title:"% do volume submetido à autenticação extra",ticksuffix:"%",range:[0,100],dtick:20},
     yaxis:{type:"linear",title:"% das fraudes alcançadas",ticksuffix:"%",range:[0,101],dtick:20}}), CFG);

  // tabela
  const cols=[["c","Canal"],["k","Categoria"],["s","Segmento"],["p","Período"],["_","× taxa geral"],["n","Transações"],["f","Fraudes"],["t","Taxa"],["vf","R$ fraude"],["pa","Volume acum."],["fa","Fraudes acum."]];
  const thead=document.querySelector("#tab thead");
  thead.innerHTML="<tr>"+cols.map(([k,n])=>`<th data-k="${k}" scope="col" class="${["c","k","s","p","_"].includes(k)?"t":""}">${n}${ordemTab.col===k?(ordemTab.dir<0?" ▾":" ▴"):""}</th>`).join("")+"</tr>";
  thead.querySelectorAll("th").forEach(th=>th.onclick=()=>{const k=th.dataset.k; if(k==="_")return; ordemTab={col:k,dir:ordemTab.col===k?-ordemTab.dir:-1}; renderDecisao();});
  const selIds=new Set(sel.map(r=>r.id));
  let lin=combos.map(r=>({...r,pa:100*r.an/t.n,fa:t.f?100*r.af/t.f:0}));
  const k=ordemTab.col;
  lin.sort((a,b)=>{ if(!!a.resto!==!!b.resto) return a.resto?1:-1; const va=a[k]??"",vb=b[k]??""; return (typeof va==="string"? String(va).localeCompare(String(vb)) : va-vb)*ordemTab.dir;});
  const maxT=Math.max(...lin.map(r=>r.t),0.0001);
  document.querySelector("#tab tbody").innerHTML = lin.map(r=>`<tr class="${selIds.has(r.id)?"corte":""}">
    ${r.resto ? `<td class="t" colspan="4"><i>Demais combinações pequenas de todos os segmentos</i></td>`
              : `<td class="t">${r.c?NOMES.c[r.c]:"<i>Demais</i>"}</td><td class="t">${r.k?NOMES.k[r.k]:"<i>Demais</i>"}</td><td class="t">${r.s}</td><td class="t">${r.p?NOMES.p[r.p].split(" ")[0]:"<i>Demais</i>"}</td>`}
    <td class="t"><span class="barra" style="width:${Math.round(46*r.t/maxT)}px"></span>${nf1.format(r.t/TAXA_GERAL)}×</td>
    <td>${nf0.format(r.n)}</td><td>${r.f}</td><td>${nf2.format(100*r.t)}%</td><td>${brl(r.vf)}</td>
    <td>${nf1.format(r.pa)}%</td><td>${nf1.format(r.fa)}%</td></tr>`).join("") || `<tr><td colspan="11">Nenhuma transação neste recorte. Limpe um dos filtros.</td></tr>`;
}

renderHora();
render();
</script>
</body>
</html>
"""

html = HTML.replace("__PLOTLY__", PLOTLY_JS).replace("__DADOS__", json.dumps(dados, ensure_ascii=False))
destino = AQUI / "dashboard.html"
destino.write_text(html, encoding="utf-8")
print(f"Dashboard gravado em {destino} ({destino.stat().st_size / 1e6:.1f} MB)")
print(f"Conferência: {int(cubo.n.sum()):,} transações, {int(cubo.f.sum()):,} fraudes, "
      f"motor atual {motor[0]:,} tx / {motor[1]} fraudes")
