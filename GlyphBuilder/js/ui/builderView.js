// Builder View (Single Responsibility: render & bind builder screen)
import { $, el } from '../core/dom.js';
import { loadSkills, saveSkills, loadSelection, saveSelection } from '../core/storage.js';
import { GLYPH_TABLE, SERIES_MAP, ALL_CATS } from '../domain/data.js';
import { computeTotals } from '../services/calculations.js';
import { pill, kpi, glyphCard } from './components.js';

const uniq = arr => [...new Set(arr)];
const flat = arr => arr.reduce((a,b)=>a.concat(b),[]);
const normalizeSkillName = (value) => String(value ?? '').trim().toLocaleLowerCase('fr');

const SERIES_INDEX = (() => {
  const map = new Map();
  Object.entries(SERIES_MAP).forEach(([label, glyphs]) => {
    const norm = normalizeSkillName(label);
    if (!norm || map.has(norm)) return;
    map.set(norm, { label, glyphs });
  });
  return map;
})();

const canonicalizeSkillName = (value) => {
  const original = String(value ?? '').trim();
  if (!original) return '';
  const norm = normalizeSkillName(original);
  return SERIES_INDEX.get(norm)?.label || original;
};

function getStoredSkills(){
  const raw = loadSkills();
  const list = Array.isArray(raw) ? raw : [];
  const seen = new Set();
  const cleaned = [];

  list.forEach((entry) => {
    const canonical = canonicalizeSkillName(entry);
    const norm = normalizeSkillName(canonical);
    if (!norm || seen.has(norm)) return;
    seen.add(norm);
    cleaned.push(canonical);
  });

  const mutated = cleaned.length !== list.length || cleaned.some((val, idx) => val !== list[idx]);
  if (mutated) saveSkills(cleaned);

  return cleaned;
}

const getUnlockedGlyphs = (skills) => uniq(flat(skills.map((s) => {
  const norm = normalizeSkillName(s);
  return SERIES_INDEX.get(norm)?.glyphs || [];
})));

export function mountBuilder(){
  renderCatTabs();
  renderSkills();
  renderGlyphs();
  renderCenterTotals();
  renderEmojiBubble();
  bindActions();
}

let CURRENT_CAT = 'Toutes';

function renderCatTabs(){
  const catTabs = $('#catTabs');
  catTabs.innerHTML = '';
  ALL_CATS.forEach(cat=>{
    const b = el('button', { class:`catBtn${CURRENT_CAT===cat?' on':''}`}, cat);
    b.addEventListener('click', ()=>{
	  CURRENT_CAT = cat;
	  renderCatTabs();   // <- redessine les boutons avec la bonne .on
	  renderGlyphs();
	});

    catTabs.appendChild(b);
  });
}

function renderSkills(){
  const skillList = $('#skillList');
  const skills = getStoredSkills();
  skillList.innerHTML='';
  skills.forEach((s,idx)=> skillList.appendChild(pill(s, ()=>{
    const arr = getStoredSkills();
    arr.splice(idx,1);
    saveSkills(arr);
    renderSkills();
    renderGlyphs();
  })));
}

function renderGlyphs(){
  const skills = getStoredSkills();
  const unlocked = new Set(getUnlockedGlyphs(skills));
  const selected = new Set(loadSelection());

  const entries = Object.entries(GLYPH_TABLE)
    .map(([name,meta])=>({name, ...meta, selected: selected.has(name)}))
    .filter(e => (unlocked.has(e.name) || e.selected) && (CURRENT_CAT==='Toutes' || e.cat===CURRENT_CAT))
    .sort((a,b)=> a.cat.localeCompare(b.cat) || a.diff-b.diff || a.name.localeCompare(b.name));

  const grid = $('#glyphGrid'); grid.innerHTML='';
  entries.forEach(e=>{
    const card = glyphCard(e, ()=>{
      const arr = loadSelection();
      const i = arr.indexOf(e.name);
      if(i>-1) arr.splice(i,1); else arr.push(e.name);
      saveSelection(arr);
      renderGlyphs();
      renderCenterTotals();
      renderEmojiBubble();
    });
    grid.appendChild(card);
  });
}

function renderCenterTotals(){
  const wrap = $('#centerTotals');
  const sel = loadSelection();
  const {mana,diff} = computeTotals(sel);
  wrap.innerHTML='';
  wrap.append(kpi('🔣 Glyphes', sel.length), kpi('🧠 Diff', diff), kpi('✨ Mana', mana));
}

function renderEmojiBubble(){
  const bubble = $('#emojiBubble');
  const sel = loadSelection();
  if(!sel.length){ bubble.textContent='(Aucune glyphe sélectionnée)'; return; }
  bubble.textContent = sel.map(n=> n.split(' ')[0] || '◻️').join(' ');
}

function bindActions(){
  const addSkillBtn = $('#addSkill');
  const clearSkillsBtn = $('#clearSkills');
  const skillInput = $('#skillInput');
  const copyBtn = $('#copyBtn');
  const resetBtn = $('#resetBtn');

  addSkillBtn?.addEventListener('click', ()=>{
    const canonical = canonicalizeSkillName(skillInput.value);
    const norm = normalizeSkillName(canonical);
    if(!norm) return;

    const skills = getStoredSkills();
    const hasSkill = skills.some(s => normalizeSkillName(s) === norm);
    if (!hasSkill) {
      skills.push(canonical);
      saveSkills(skills);
    }
    skillInput.value='';
    renderSkills();
    renderGlyphs();
  });

  clearSkillsBtn?.addEventListener('click', ()=>{
    if(confirm('Effacer toutes les compétences enregistrées ?')){
      saveSkills([]); renderSkills(); renderGlyphs();
    }
  });

  copyBtn?.addEventListener('click', ()=>{
    const text = loadSelection().map(n => n.split(' ')[0]).join(' ');
    navigator.clipboard.writeText(text).then(()=>{
      copyBtn.textContent='✅ Copié !'; setTimeout(()=>copyBtn.textContent='📋 Copier',1200);
    });
  });

  resetBtn?.addEventListener('click', ()=>{
    if(confirm('Réinitialiser la sélection active ?')){
      saveSelection([]); renderGlyphs(); renderCenterTotals(); renderEmojiBubble();
    }
  });
}