
(() => {
  const SUPPORTED = ["bg", "hr", "cs", "da", "nl", "en", "et", "fi", "fr", "de", "el", "hu", "it", "lv", "lt", "ga", "mt", "pl", "pt", "ro", "sk", "sl", "es", "sv", "cy", "uk", "ru", "fa"];
  const RTL = new Set(['fa','ar','he','ur','ps']);
  const DEFAULT_LANG = 'en';

  function mapToSupported(lang) {
    if (!lang) return DEFAULT_LANG;
    lang = lang.toLowerCase();
    const base = lang.split('-')[0];
    if (SUPPORTED.includes(lang)) return lang;
    if (SUPPORTED.includes(base)) return base;
    return DEFAULT_LANG;
  }

  async function loadLocale(lang) {
    const res = await fetch(`./locales/${lang}.json`, {cache:'no-cache'});
    if (!res.ok) throw new Error('Locale load failed: ' + lang);
    return res.json();
  }

  function format(str, vars) {
    return str.replace(/\{\{(\w+)\}\}/g, (_, k) => (vars && (k in vars)) ? String(vars[k]) : '');
  }

  function applyI18n(dict) {
    const year = new Date().getFullYear();
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      const val = key.split('.').reduce((o,k)=>o&&o[k], dict);
      if (typeof val === 'string') {
        el.textContent = format(val, {year});
      }
    });
  }

  async function init() {
    let lang = localStorage.getItem('lang')
      || (navigator.languages && navigator.languages[0])
      || navigator.language
      || DEFAULT_LANG;
    lang = mapToSupported(lang);

    document.documentElement.lang = lang;
    document.documentElement.dir = RTL.has(lang) ? 'rtl' : 'ltr';

    try {
      const dict = await loadLocale(lang);
      applyI18n(dict);
      const select = document.getElementById('lang');
      if (select) select.value = lang;
    } catch (e) {
      if (lang !== DEFAULT_LANG) {
        const dict = await loadLocale(DEFAULT_LANG);
        applyI18n(dict);
      }
    }
  }

  window.addEventListener('DOMContentLoaded', () => {
    const sel = document.getElementById('lang');
    if (sel) {
      sel.innerHTML = '<option value="bg">bg</option><option value="hr">hr</option><option value="cs">cs</option><option value="da">da</option><option value="nl">nl</option><option value="en">en</option><option value="et">et</option><option value="fi">fi</option><option value="fr">fr</option><option value="de">de</option><option value="el">el</option><option value="hu">hu</option><option value="it">it</option><option value="lv">lv</option><option value="lt">lt</option><option value="ga">ga</option><option value="mt">mt</option><option value="pl">pl</option><option value="pt">pt</option><option value="ro">ro</option><option value="sk">sk</option><option value="sl">sl</option><option value="es">es</option><option value="sv">sv</option><option value="cy">cy</option><option value="uk">uk</option><option value="ru">ru</option><option value="fa">fa</option>';
      sel.addEventListener('change', () => {
        const lang = sel.value;
        localStorage.setItem('lang', lang);
        location.reload();
      });
    }
    init();
  });
})();
