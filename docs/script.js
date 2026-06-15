// ===========================================================
//  MISMATHE — landing site interactivity
//  Pure client-side. No backend, no API key. Deploys anywhere.
// ===========================================================
'use strict';

/* ----- 7 mentor modes ----- */
const MODES = [
  { emoji: '🔥', label: 'Strict',     color: '#ef4444', when: 'When you need a push',   desc: 'High discipline, sharp accountability, no-excuses urgency. The coach who won\'t let you settle.' },
  { emoji: '🧘', label: 'Calm',       color: '#22d3ee', when: 'Overwhelmed days',        desc: 'Soft, grounding, stress-reducing. Your worth isn\'t your marks — breathe, slow down, take one step.' },
  { emoji: '🚀', label: 'Motivation', color: '#a855f7', when: 'Confidence dip',          desc: 'Vision-forward, identity-building. Feel the version of yourself who has already won.' },
  { emoji: '🩹', label: 'Recovery',   color: '#10b981', when: 'Fell off track',          desc: 'Zero-guilt restart. The past is dead — today is a clean slate. One tiny first step.' },
  { emoji: '🎯', label: 'Challenge',  color: '#f59e0b', when: 'Want a game',             desc: 'Gamified missions, streaks, XP energy. "Boss fight: 50 mock questions in 60 min — accept?"' },
  { emoji: '🎧', label: 'Focus',      color: '#6366f1', when: 'Deep work',               desc: 'Minimal words, single task, zero distraction. Pure execution. Get INTO the work.' },
  { emoji: '🤝', label: 'Friend',     color: '#ec4899', when: 'Default mode',            desc: 'Casual Gen-Z best-friend energy. Understood first, corrected second. Connection over everything.' },
];

/* ----- Class 11 syllabus (Maharashtra Board) — marks / with-option ----- */
const SYLLABUS = {
  Physics: [
    ['Units and Measurements', 5, 7], ['Mathematical Methods', 5, 7], ['Motion in a Plane', 6, 8],
    ['Laws of Motion', 7, 10], ['Gravitation', 5, 7], ['Mechanical Properties of Solids', 4, 6],
    ['Thermal Properties of Matter', 5, 7], ['Sound', 5, 7], ['Optics', 7, 10],
    ['Electrostatics', 5, 7], ['Electric Current Through Conductors', 4, 6], ['Magnetism', 4, 6],
    ['Electromagnetic Waves and Communication System', 4, 5], ['Semiconductors', 4, 5],
  ],
  Chemistry: [
    ['Some Basic Concepts of Chemistry', 3, 5], ['Introduction to Analytical Chemistry', 4, 6],
    ['Basic Analytical Techniques', 2, 3], ['Structure of Atom', 5, 7], ['Chemical Bonding', 6, 8],
    ['Redox Reaction', 3, 4], ['Modern Periodic Table', 4, 6], ['Elements of Group 1 and 2', 4, 6],
    ['Elements of Group 13, 14 and 15', 6, 8], ['States of Matter', 4, 6], ['Adsorption and Colloids', 3, 4],
    ['Chemical Equilibrium', 6, 8], ['Nuclear Chemistry and Radioactivity', 3, 4],
    ['Basic Principles of Organic Chemistry', 6, 8], ['Hydrocarbons', 8, 11], ['Chemistry in Everyday Life', 3, 4],
  ],
  Mathematics: [
    ['Angle and its Measurement', 3, 4], ['Trigonometry - I', 4, 6], ['Trigonometry - II', 6, 8],
    ['Determinants and Matrices', 7, 10], ['Straight Line', 4, 5], ['Circle', 3, 4],
    ['Conic Sections', 6, 8], ['Measures of Dispersion', 4, 5], ['Probability', 4, 6],
    ['Complex Numbers', 4, 6], ['Sequences and Series', 5, 7], ['Permutations and Combinations', 6, 8],
    ['Methods of Induction and Binomial Theorem', 5, 7], ['Sets and Relations', 4, 6],
    ['Functions', 4, 5], ['Limits', 4, 6], ['Continuity', 3, 5], ['Differentiation', 4, 6],
  ],
};

/* top-6 by marks-with-option */
function topPriority(subject, n = 6) {
  return [...SYLLABUS[subject]]
    .sort((a, b) => b[2] - a[2])
    .slice(0, n)
    .map((c) => c[0]);
}

const $ = (id) => document.getElementById(id);

/* ----- render mentor modes ----- */
function renderModes() {
  const grid = $('modesGrid');
  grid.innerHTML = MODES.map((m) => `
    <div class="mode-card" style="--mode-color:${m.color}">
      <div class="mode-emoji">${m.emoji}</div>
      <h3>${m.label}</h3>
      <div class="mode-when">${m.when}</div>
      <p>${m.desc}</p>
    </div>`).join('');
}

/* ----- render syllabus panel for a subject ----- */
let priorityCache = {};
function renderSyllabus(subject) {
  const priority = new Set(topPriority(subject));
  priorityCache[subject] = priority;
  $('syllabusPanel').innerHTML = SYLLABUS[subject].map((c, i) => {
    const [name, marks, withOpt] = c;
    const star = priority.has(name);
    return `
      <div class="chap ${star ? 'star' : ''}">
        <span class="chap-name"><span class="num">${i + 1}.</span>${name}</span>
        <span class="chap-marks">
          <span class="marks-pill">${marks}/${withOpt}</span>
          ${star ? '<span class="star-badge" title="High priority">⭐</span>' : ''}
        </span>
      </div>`;
  }).join('');
}

/* ----- render the top-6 priority box (all subjects) ----- */
function renderPriority() {
  $('priorityGrid').innerHTML = Object.keys(SYLLABUS).map((subject) => `
    <div class="pri-col">
      <h4>${subject}</h4>
      <ol>${topPriority(subject).map((c) => `<li>${c}</li>`).join('')}</ol>
    </div>`).join('');
}

/* ----- tab switching ----- */
function wireTabs() {
  document.querySelectorAll('.tab').forEach((tab) => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach((t) => t.classList.remove('active'));
      tab.classList.add('active');
      renderSyllabus(tab.dataset.subject);
    });
  });
}

/* ----- reveal-on-scroll ----- */
function wireReveal() {
  const els = document.querySelectorAll(
    '.principle, .mode-card, .feature, .cta-card, .priority-box, .syllabus-tabs'
  );
  els.forEach((el) => el.classList.add('reveal'));
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
    });
  }, { threshold: 0.08 });
  els.forEach((el) => io.observe(el));
}

/* ----- boot ----- */
document.addEventListener('DOMContentLoaded', () => {
  renderModes();
  renderSyllabus('Physics');
  renderPriority();
  wireTabs();
  wireReveal();
});
