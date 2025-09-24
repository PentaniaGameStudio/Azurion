// Analyzer service (Single Responsibility: parse and match inputs)
import { GLYPH_TABLE } from '../domain/data.js';
import { computeTotals } from './calculations.js';

const EMOJI_MAP = {};     // emoji -> glyph name
const NAME_LIST = [];     // [{name, norm}]
(function prep(){
  Object.keys(GLYPH_TABLE).forEach(n=>{
    const emoji = (n.split(' ')[0] || '').trim();
    if(emoji) EMOJI_MAP[emoji] = n;
    NAME_LIST.push({name:n, norm:normalize(n)});
  });
})();

export function normalize(s){
  return s.toLowerCase()
    .normalize('NFD').replace(/[\u0300-\u036f]/g,'')
    .replace(/[^\p{L}\p{N}\s]/gu,' ')
    .replace(/\s+/g,' ').trim();
}

export function tokenize(raw){
  const emojis = [...raw.matchAll(/[\p{Emoji_Presentation}\p{Emoji}\uFE0F\u200D]+/gu)].map(m=>m[0]);
  let text = raw; emojis.forEach(e=> text = text.split(e).join(' '));
  const parts = text.split(/[,|·;\/\n]+/).map(t=>t.trim()).filter(Boolean);
  const words = parts.flatMap(p => p.split(/\s+/)).filter(Boolean);
  return {emojis, parts, words};
}

function findByEmoji(emojiList){ return emojiList.map(e=>EMOJI_MAP[e]).filter(Boolean); }
function findByExactPart(parts){
  const found = [];
  parts.forEach(p=>{
    const norm = normalize(p);
    const hit = NAME_LIST.find(x => x.norm === norm);
    if(hit) found.push(hit.name);
  });
  return found;
}
function findByFuzzyWords(words){
  const found = new Set();
  const kws = words.map(normalize).filter(w=>w.length>=3);
  NAME_LIST.forEach(x=>{ if(kws.length && kws.some(w=> x.norm.includes(w))) found.add(x.name); });
  return [...found];
}

const uniq = arr => [...new Set(arr)];

export function analyzeInput(raw){
  const {emojis, parts, words} = tokenize(raw);
  const byEmoji = findByEmoji(emojis);
  const byExact = findByExactPart(parts);
  const byFuzzy = findByFuzzyWords(words);

  const score = new Map();
  const add=(n,s)=>score.set(n, Math.max(score.get(n)||0, s));
  byEmoji.forEach(n=>add(n,3));
  byExact.forEach(n=>add(n,2));
  byFuzzy.forEach(n=>add(n,1));

  const detected = uniq([...score.entries()].filter(([n,s])=> s>=2).sort((a,b)=>b[1]-a[1]).map(([n])=>n));
  const unknown = [];
  emojis.forEach(e=>{ if(!EMOJI_MAP[e]) unknown.push(e); });
  parts.forEach(p=>{ const norm=normalize(p); if(!NAME_LIST.some(x=>x.norm===norm) && norm.length>=3) unknown.push(p); });

  const {mana,diff} = computeTotals(detected);
  return {detected, unknown, mana, diff};
}