// --- Données de référence --------------------------------------------------
export const GLYPH_TABLE = {
  // palier difficulté ~5
  "🔥 Feu":{diff:5,mana:0.3, cat:"Éléments"},
  "💧 Eau":{diff:5,mana:0.3, cat:"Éléments"},
  "🏔 Terre":{diff:5,mana:0.3, cat:"Éléments"},
  "🌪 Vent":{diff:5,mana:0.3, cat:"Éléments"},
  "💚 Soin":{diff:5,mana:0.3, cat:"Éléments"},
  "❄️ Glace":{diff:5,mana:0.3, cat:"Éléments"},
  "⚡ Foudre":{diff:5,mana:0.3, cat:"Éléments"},
  "🎯 Cible unique":{diff:5,mana:0.3, cat:"Ciblage"},
  "🌌 Zone":{diff:5,mana:0.5, cat:"Ciblage"},
  "🔜 Cible la plus proche":{diff:5,mana:0.3, cat:"Ciblage"},
  "↩️ Utilisateur":{diff:5,mana:0.5, cat:"Ciblage"},
  "💀 Affaiblissement":{diff:5,mana:0.5, cat:"États"},
  "💫 Étourdissement":{diff:5,mana:0.5, cat:"États"},
  "🧊 Gel":{diff:5,mana:0.5, cat:"États"},
  "🫧 Poison":{diff:5,mana:0.5, cat:"États"},
  "💪 Physique":{diff:5,mana:0.5, cat:"Amplification"},
  "💬 Social":{diff:5,mana:0.5, cat:"Amplification"},
  "🧠 Mental":{diff:5,mana:0.5, cat:"Amplification"},
  "💥 Destruction":{diff:5,mana:0.5, cat:"Actions"},
  "🤚 Contact":{diff:5,mana:0.5, cat:"Actions"},

  // palier difficulté ~10
  "🟣 Ombre":{diff:10,mana:0.5, cat:"Éléments"},
  "☀️ Lumière":{diff:10,mana:0.5, cat:"Éléments"},
  "🌱 Nature":{diff:10,mana:0.5, cat:"Éléments"},
  "💙 Bénédiction":{diff:10,mana:0.5, cat:"Éléments"},
  "🛜 Conique":{diff:10,mana:0.5, cat:"Ciblage"},
  "↕️ Ligne (4m)":{diff:10,mana:0.5, cat:"Ciblage"},
  "🔢 Multi-cible (jusqu’à 4)":{diff:10,mana:0.4, cat:"Ciblage"},
  "👥 Chaîne":{diff:10,mana:0.4, cat:"Ciblage"},
  "🔥 Brûlure":{diff:10,mana:0.5, cat:"États"},
  "💤 Sommeil":{diff:10,mana:0.5, cat:"États"},
  "🌀 Confusion":{diff:10,mana:0.5, cat:"États"},
  "🛡 Défensif":{diff:10,mana:0.5, cat:"Actions"},
  "⚔️ Offensif":{diff:10,mana:0.5, cat:"Actions"},

  // palier difficulté ~20
  "🩸 Sang":{diff:20,mana:0.75, cat:"Éléments"},
  "🪞 Illusion":{diff:20,mana:0.75, cat:"Éléments"},
  "💀 Nécromantie":{diff:20,mana:0.75, cat:"Éléments"},
  "🎶 Sons":{diff:20,mana:0.75, cat:"Éléments"},
  "🌐 Toute entitée":{diff:20,mana:1, cat:"Ciblage"},
  "👍 Allié":{diff:20,mana:1, cat:"Ciblage"},
  "👎 Ennemi":{diff:20,mana:1, cat:"Ciblage"},
  "❤️ Charme":{diff:20,mana:1, cat:"États"},
  "🤐 Silence":{diff:20,mana:0.5, cat:"États"},
  "👁‍🗨 Cécité":{diff:20,mana:0.5, cat:"États"},
  "🪬 Marquage":{diff:20,mana:0.5, cat:"Actions"},

  // palier difficulté ~40
  "🕚 Temporel":{diff:40,mana:1.5, cat:"Éléments"},
  "🌌 Cosmique":{diff:40,mana:1.5, cat:"Éléments"},
  "🎲 Aléatoire":{diff:40,mana:1, cat:"Ciblage"},
  "🧭 Directionnel":{diff:40,mana:0.5, cat:"Ciblage"},
  "🔼 Power-Up":{diff:40,mana:2, cat:"Amplification"},
  "🔽 Power-Down":{diff:40,mana:2, cat:"Amplification"},
  "➕ Puissance":{diff:40,mana:2, cat:"Amplification"},
  "📏 Portée":{diff:40,mana:2, cat:"Amplification"},
  "⏳ Durée":{diff:40,mana:2, cat:"Amplification"},
  "💣 Explosion":{diff:40,mana:2, cat:"Actions"},

  // palier difficulté ~80 / Maître
  "🪦 Mort":{diff:80,mana:3, cat:"Éléments"},
  "🐦‍🔥 Résurection":{diff:80,mana:3, cat:"Éléments"},
  "📍 Persistante (zone)":{diff:80,mana:1, cat:"Ciblage"},
  "📊 Répétition":{diff:80,mana:2, cat:"Amplification"},
  "✴️ Création":{diff:80,mana:4, cat:"Amplification"},
  "🕧 Retardement":{diff:80,mana:2, cat:"Actions"},
  "💯 Critique":{diff:80,mana:3, cat:"Contrôle"},
  "🎲 Variance":{diff:80,mana:3, cat:"Contrôle"},

  // Ultime
  "♾️ Infinité":{diff:160,mana:5, cat:"Ultime"},
  "🌒 Éclipse":{diff:160,mana:5, cat:"Ultime"}
};

export const CATEGORIES = ["Éléments","Ciblage","États","Amplification","Actions","Contrôle","Ultime"];
