// Display catalog for the persona picker. The backend owns the real FI data;
// these are just friendly labels for the five synthetic personas.

export interface PersonaCard {
  id: string;
  name: string;
  age: number;
  emoji: string;
  tagline: string;
}

export const PERSONAS: PersonaCard[] = [
  {
    id: "young_spender",
    name: "Aarav Sharma",
    age: 27,
    emoji: "🍔",
    tagline: "Big on food delivery, no SIP yet.",
  },
  {
    id: "disciplined_saver",
    name: "Priya Nair",
    age: 34,
    emoji: "📈",
    tagline: "Regular SIP, saves with discipline.",
  },
  {
    id: "idle_cash",
    name: "Rajesh Menon",
    age: 41,
    emoji: "💤",
    tagline: "Lakhs sitting idle in savings.",
  },
  {
    id: "over_insured",
    name: "Sunita Rao",
    age: 38,
    emoji: "🛡️",
    tagline: "Insurance-heavy, thin on equity.",
  },
  {
    id: "near_retiree",
    name: "Mohan Kulkarni",
    age: 54,
    emoji: "🏦",
    tagline: "FD-rich, nearing retirement.",
  },
];
