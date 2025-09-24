// Analyzer View (Single Responsibility: render & bind analyzer screen)
import { $, el } from '../core/dom.js';
import { analyzeInput } from '../services/analyzer.js';
import { GLYPH_TABLE } from '../domain/data.js';
import { loadSelection, saveSelection } from '../core/storage.js';

export function mountAnalyzer(){
  bindAnalyzerUI();
}

function bindAnalyzerUI(){
  const anInput = $('#anInput');
  const anPaste = $('#anPaste');
  const anRun = $('#anRun');
  const anAddToSel = $('#anAddToSel');

  anPaste.addEventListener('click', async ()=>{
    try{ anInput.value = await navigator.clipboard.readText(); }
    catch{ alert('Impossible d\'accéder au presse-papier. Colle manuellement (Ctrl+V).'); }
  });

  anRun.addEventListener('click', ()=>{
    const raw = (anInput.value||'').trim();
    const res = raw ? analyzeInput(raw) : {detected:[],unknown:[],mana:0,diff:0};
    renderAnalysis(res);
  });

  anAddToSel.addEventListener('click', ()=>{
    const chips = [...document.querySelectorAll('#anDetectedChips .chip')].map(c=>c.textContent);
    const merged = [...new Set(loadSelection().concat(chips))];
    saveSelection(merged);
    // Feedback
    anAddToSel.textContent = '✅ Ajouté'; setTimeout(()=> anAddToSel.textContent='➕ Ajouter à la sélection', 900);
  });
}

function renderAnalysis(res){
  const anBubble = $('#anBubble');
  const anTotals = $('#anTotals');
  const anDetectedChips = $('#anDetectedChips');
  const anUnknownChips = $('#anUnknownChips');
  const anTableBody = document.querySelector('#anTable tbody');
  const anAddToSel = $('#anAddToSel');

  anBubble.textContent = res.detected.length ? res.detected.map(n=> n.split(' ')[0]).join(' ') : '(aucune glyphe détectée)';

  anTotals.innerHTML = '';
  anTotals.append(
    el('div',{class:'kpi'}, el('span',{class:'muted'},'🔣 Glyphes'), el('b',{class:'mono'}, String(res.detected.length))),
    el('div',{class:'kpi'}, el('span',{class:'muted'},'🧪 Diff'), el('b',{class:'mono'}, String(res.diff))),
    el('div',{class:'kpi'}, el('span',{class:'muted'},'💧 Mana'), el('b',{class:'mono'}, String(res.mana)))
  );

  anDetectedChips.innerHTML='';
  res.detected.forEach(n=> anDetectedChips.appendChild(el('div',{class:'chip'}, n)));

  anUnknownChips.innerHTML='';
  if(res.unknown.length===0) anUnknownChips.appendChild(el('div',{class:'chip'}, '—'));
  else res.unknown.forEach(u=> anUnknownChips.appendChild(el('div',{class:'chip'}, u)));

  anTableBody.innerHTML='';
  res.detected.forEach(n=>{
    const d = GLYPH_TABLE[n];
    const tr = el('tr',{},
      el('td',{},n),
      el('td',{},d?.cat||'?'),
      el('td',{class:'mono'}, d?.diff??'?'),
      el('td',{class:'mono'}, d?.mana??'?')
    );
    anTableBody.appendChild(tr);
  });

  anAddToSel.disabled = res.detected.length===0;
}