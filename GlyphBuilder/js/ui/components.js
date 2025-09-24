// UI component factory (Dependency Inversion: accepts services via params)
import { el } from '../core/dom.js';

export const pill = (label, onRemove) => {
  const root = el('span', { class:'pill' }, label);
  if(onRemove){
    const x = el('button', {}, '✖');
    x.addEventListener('click', (e)=>{ e.stopPropagation(); onRemove(); });
    root.append(' ', x);
  }
  return root;
};

export const kpi = (label, value) => el('div', { class:'kpi' }, el('span',{class:'muted'},label), el('b',{class:'mono'}, String(value)));

export function glyphCard(entry, onToggle){
  const {name, cat, diff, mana, selected} = entry;
  const card = el('div', { class:`glyph${selected?' on':''}`});
	const meta = el('div', { class:'meta' },
	  el('div',{class:'name'}, name),
	  el('div',{class:'sub'}, cat),
	  el('div',{class:'sub'}, `🧠 ${diff}   •  ✨ ${mana}`),
	);

  card.addEventListener('click', onToggle);
	card.append(meta);

  return card;
}