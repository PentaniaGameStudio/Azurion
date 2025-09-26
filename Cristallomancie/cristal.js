/// <summary>
/// Calculateur de Cristallomancie — logique principale
/// Stabilité RÉDUIT la fragilité (bonus).
/// </summary>

const CONFIG = {
  // Rang: baseTier = palier offert partout + coût de difficulté
  rank: {
    ECLAT:  { label:"Éclat",  diff:10, baseTier:0 },
    PIERRE: { label:"Pierre", diff:20, baseTier:1 },
    COEUR:  { label:"Cœur",   diff:40, baseTier:2 },
  },

  // Affinage: budget de points + coût de difficulté
  // NOTE: tu peux repasser à 10/10 (Épurée/Sublimée) si tu préfères.
  refine: {
    BRUTE:    { label:"Brute",    diff:10, points:0  },
    EPUREE:   { label:"Épurée",   diff:20, points:26 },
    SUBLIMEE: { label:"Sublimée", diff:40, points:48 },
  },

  // Qualités
  qualities: [
    { key:"puissance", label:"Puissance", hint:"Force de l’attaque / quantité de mana" },
    { key:"portee",    label:"Portée",    hint:"Distance d’utilisation/transfert" },
    { key:"duree",     label:"Durée",     hint:"Temps d’effet (si applicable)" },
    { key:"controle",  label:"Contrôle",  hint:"Modelage / précision des effets (Cible / Zone / Nuage / Etc)" },
	{ key:"stabilite", label:"Stabilité",  hint:"Renforce la pierre, réduit la fragilité" },
  ],

  // Paliers 0→5
  tier: { min:0, max:5 },

  // Coût en POINTS pour chaque montée de palier (exponentiel raisonnable)
  // 0→1=1, 1→2=2, 2→3=3, 3→4=5, 4→5=8
  pointsStepCost: [1,2,3,5,8],

  // Coût en DIFFICULTÉ pour chaque montée de palier (légèrement exponentiel)
  diffStepCost:   [2,3,4,6,9],

  // Fragilité (score → bande d'utilisations)
	fragility: {
	  /// <summary>Score = Σ (tier^2) - bonusDiversification - bonusStabilité</summary>
	  diversificationBonusPerQuality: 2,
	  stabilityBonusPerTier: 8,           // chaque palier de Stabilité réduit la fragilité
	  bands: [
		{ max: 14, label:"Faible (5)", uses:5 },
		{ max: 22, label:"Moyenne (3)", uses:3 },
		{ max: 30, label:"Haute (2)", uses:2 },
		{ max:  1e9, label:"Critique (1)", uses:1 },
	  ]
	}

};
/// <summary>Mise à jour du remplissage (WebKit) via CSS var --fill</summary>
function updateFill(range){
  const min = Number(range.min) || 0;
  const max = Number(range.max) || 100;
  const val = Number(range.value) || 0;
  const pct = max > min ? ((val - min) / (max - min)) * 100 : 0;
  range.style.setProperty('--fill', pct + '%');
}

/// <summary>MàJ du remplissage pour tous les sliders</summary>
function updateAllFills(){
  document.querySelectorAll('#qualities input[type="range"]').forEach(updateFill);
}

/// <summary>État courant.</summary>
const state = {
  rank: "ECLAT",
  refine: "BRUTE",
  tiers: Object.fromEntries(CONFIG.qualities.map(q => [q.key, 0])),
};

/// <summary>Palier de base selon le rang.</summary>
function getBaseTier() { return CONFIG.rank[state.rank].baseTier; }

/// <summary>Budget de points selon l’affinage.</summary>
function getPointBudget() { return CONFIG.refine[state.refine].points; }

/// <summary>Remet toutes les qualités au palier de base.</summary>
function resetToBase() {
  const base = getBaseTier();
  for (const k in state.tiers) state.tiers[k] = base;
}

/// <summary>Coût en POINTS de from→to (somme des steps).</summary>
function pointsCostBetween(from, to) {
  let cost = 0;
  for (let t = from; t < to; t++) cost += (CONFIG.pointsStepCost[t] ?? 9999);
  return cost;
}

/// <summary>Coût en DIFFICULTÉ de from→to (somme des steps).</summary>
function diffCostBetween(from, to) {
  let cost = 0;
  for (let t = from; t < to; t++) cost += (CONFIG.diffStepCost[t] ?? 0);
  return cost;
}

/// <summary>Total points dépensés au-dessus du palier de base.</summary>
function computePointsSpent() {
  const base = getBaseTier();
  let sum = 0;
  for (const k in state.tiers) {
    const t = state.tiers[k];
    if (t > base) sum += pointsCostBetween(base, t);
  }
  return sum;
}

/// <summary>Diff. ajoutée par les paliers au-dessus de la base.</summary>
function computeDiffFromTiers() {
  const base = getBaseTier();
  let sum = 0;
  for (const k in state.tiers) {
    const t = state.tiers[k];
    if (t > base) sum += diffCostBetween(base, t);
  }
  return sum;
}

function computeFragilityScore() {
  // Σ(tier^2) SANS compter la Stabilité
  const sumSquares = Object.entries(state.tiers)
    .reduce((acc, [k, v]) => acc + (k === "stabilite" ? 0 : v * v), 0);

  const nonZeroCount = Object.values(state.tiers).filter(t => t > 0).length;
  const diversif = nonZeroCount * CONFIG.fragility.diversificationBonusPerQuality;

  const stabTier = state.tiers["stabilite"] ?? 0;
  const stabBonus = stabTier * CONFIG.fragility.stabilityBonusPerTier;

  // Plus le score est bas → plus c'est robuste.
  return Math.max(0, sumSquares - diversif - stabBonus);
}



/// <summary>Map score → bande (label + uses).</summary>
function fragilityBand(score) {
  for (const b of CONFIG.fragility.bands) if (score <= b.max) return b;
  return CONFIG.fragility.bands.at(-1);
}

/// <summary>Essaye de fixer le palier d’une qualité (respect du budget).</summary>
function trySetTier(key, newTier) {
  const base = getBaseTier();
  const prev = state.tiers[key];
  newTier = Math.max(CONFIG.tier.min, Math.min(CONFIG.tier.max, newTier));
  newTier = Math.max(newTier, base); // pas sous le palier de base

  const spentNow = computePointsSpent();
  const budget = getPointBudget();
  const deltaCost = newTier > prev ? pointsCostBetween(prev, newTier)
                                   : -pointsCostBetween(newTier, prev);

  if (deltaCost <= 0) { state.tiers[key] = newTier; return true; }    // baisser = toujours OK
  if (spentNow + deltaCost <= budget) { state.tiers[key] = newTier; return true; }
  return false; // manque de points
}

/// <summary>Reconstruit les sliders des qualités.</summary>
function buildQualitiesUI() {
  const root = document.getElementById('qualities');
  root.innerHTML = "";
  const base = getBaseTier();

  CONFIG.qualities.forEach(q => {
    const row = document.createElement('div');
    row.className = 'quality';
    row.innerHTML = `
      <div>
        <div class="qname">${q.label}</div>
        <div class="qhint">${q.hint}</div>
      </div>
      <input type="range" min="${base}" max="${CONFIG.tier.max}" step="1" value="${state.tiers[q.key]}"/>
      <div class="pill"><span id="val-${q.key}">${state.tiers[q.key]}</span> / 5</div>
    `;
    const range = row.querySelector('input[type="range"]');
    const val   = row.querySelector(`#val-${q.key}`);

    // Forcer la valeur courante (visuel)
    range.value = state.tiers[q.key];
    val.textContent = range.value;
	updateFill(range);

    range.addEventListener('input', () => {
      const want = parseInt(range.value,10);
      if (!trySetTier(q.key, want)) {
        range.value = state.tiers[q.key]; // rollback si dépassement budget
      }
      val.textContent = range.value;
	  updateFill(range);

      refreshOutputs();
    });

    root.appendChild(row);
  });
}

/// <summary>Met à jour KPI, total, fragilité, résumé.</summary>
function refreshOutputs() {
  const spent = computePointsSpent();
  const budget = getPointBudget();
  document.getElementById('spent').textContent = spent;
  document.getElementById('remain').textContent = Math.max(0, budget - spent);

  const dRank = CONFIG.rank[state.rank].diff;
  const dRef  = CONFIG.refine[state.refine].diff;
  const dQual = computeDiffFromTiers();
  const total = dRank + dRef + dQual;

  document.getElementById('kpi-rank').textContent = dRank;
  document.getElementById('kpi-refine').textContent = dRef;
  document.getElementById('kpi-qdif').textContent = dQual;
  document.getElementById('total').textContent = total;

  const score = computeFragilityScore();
  const band = fragilityBand(score);
  document.getElementById('fragility').textContent = band.label;

  const base = getBaseTier();
  const parts = [];
  for (const q of CONFIG.qualities) {
    const t = state.tiers[q.key];
    parts.push(`${q.label} ${t}${t>base ? ` (+${t-base})` : ""}`);
  }
  document.getElementById('summary').textContent =
    `Rang ${CONFIG.rank[state.rank].label} (base ${base}) • ${CONFIG.refine[state.refine].label} (${budget} pts) • ` +
    parts.join(", ") + `. Difficulté ${total}.`;
}

/// <summary>Export texte: "Rang Affinage (Pu Po Du Co St) : Utilisation" → copie presse-papier</summary>
function exportText() {
  const r = CONFIG.rank[state.rank].label;
  const f = CONFIG.refine[state.refine].label;
  const abbr = { puissance:"Pu", portee:"Po", duree:"Du", controle:"Co", stabilite:"St" };
  const inside = Object.keys(abbr).map(k => `${abbr[k]}${state.tiers[k]}`).join(" ");
  const band = fragilityBand(computeFragilityScore());
  const line = `${r} ${f} (${inside}) : ${band.uses}`;

  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(line);
  } else {
    // Fallback (HTTP/localfile)
    const ta = document.createElement('textarea');
    ta.value = line;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand('copy'); } catch(e) {}
    document.body.removeChild(ta);
  }
}


/// <summary>Petit bump visuel sur les lignes de qualité.</summary>
function bumpQualities() {
  document.querySelectorAll('#qualities .quality').forEach(row => {
    row.classList.remove('bump');
    void row.offsetWidth; // reflow
    row.classList.add('bump');
  });
}

/// <summary>Init + listeners.</summary>
function init() {
  resetToBase();
  buildQualitiesUI();
  document.getElementById('rank').addEventListener('change', e=>{
    state.rank = e.target.value;
    resetToBase();      // sliders montent au palier de base
    buildQualitiesUI(); // min = base, value = base
    refreshOutputs();
    bumpQualities();    // feedback visuel
  });
  document.getElementById('refine').addEventListener('change', e=>{
    state.refine = e.target.value;
    refreshOutputs();
  });
  document.getElementById('btn-reset').addEventListener('click', ()=>{
    resetToBase();
    buildQualitiesUI();
    refreshOutputs();
  });
  document.getElementById('btn-export').addEventListener('click', exportText);
  refreshOutputs();
}

document.addEventListener('DOMContentLoaded', init);
