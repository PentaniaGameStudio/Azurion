// /PotionBuilder/js/core/events.js
const topics = new Map(); // topic -> Set<handler>

/** @param {string} topic @param {(data:any)=>void} handler */
export function sub(topic, handler) {
  if (!topics.has(topic)) topics.set(topic, new Set());
  topics.get(topic).add(handler);
  return () => topics.get(topic)?.delete(handler);
}

/** @param {string} topic @param {any} data */
export function pub(topic, data) {
  const set = topics.get(topic);
  if (!set) return;
  set.forEach(h => {
    try { h(data); } catch (e) { console.error(`[events] handler error for ${topic}`, e); }
  });
}

/** Convenience: one-time subscription */
export function once(topic, handler){
  const off = sub(topic, (d)=>{ off(); handler(d); });
}
