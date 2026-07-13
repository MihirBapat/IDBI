// Display catalog for the persona picker. The backend owns the real FI data;
// these are just friendly labels for the synthetic personas.

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
  {
    id: "new_graduate",
    name: "Ishaan Verma",
    age: 23,
    emoji: "🎓",
    tagline: "First job, student loan, starting out.",
  },
  {
    id: "credit_revolver",
    name: "Rohan Kapoor",
    age: 31,
    emoji: "💳",
    tagline: "Lifestyle spend, EMIs, thin savings.",
  },
  {
    id: "dinks_couple",
    name: "Neha Malhotra",
    age: 33,
    emoji: "💑",
    tagline: "Dual income, big SIP, strong surplus.",
  },
  {
    id: "sandwich_generation",
    name: "Deepak Iyer",
    age: 45,
    emoji: "🥪",
    tagline: "Supporting parents and kids at once.",
  },
  {
    id: "fd_loyalist",
    name: "Lakshmi Pillai",
    age: 48,
    emoji: "🔒",
    tagline: "Everything in FDs, cash idling.",
  },
  {
    id: "rural_saver",
    name: "Kavya Reddy",
    age: 40,
    emoji: "🌾",
    tagline: "Frugal saver, no equity yet.",
  },
  {
    id: "single_parent",
    name: "Meera Joshi",
    age: 36,
    emoji: "👩‍👧",
    tagline: "Single mom, school fees, tight budget.",
  },
  {
    id: "fire_aspirant",
    name: "Aditya Ghosh",
    age: 43,
    emoji: "🔥",
    tagline: "Aggressive saver chasing early retirement.",
  },
  {
    id: "self_employed_business",
    name: "Vikram Shah",
    age: 47,
    emoji: "🏪",
    tagline: "Business owner, lumpy cash, thin equity.",
  },
  {
    id: "senior_pensioner",
    name: "Ramesh Gupta",
    age: 61,
    emoji: "👴",
    tagline: "Retired on pension, FD-heavy.",
  },
];
