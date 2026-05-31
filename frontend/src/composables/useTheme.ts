import { ref, watch } from 'vue'

type Theme = 'dark' | 'frost'

const STORAGE_KEY = 'ski-theme'
const theme = ref<Theme>(loadTheme())

function loadTheme(): Theme {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored === 'frost' || stored === 'dark') return stored
  } catch {}
  return 'dark'
}

function applyTheme(t: Theme) {
  document.documentElement.setAttribute('data-theme', t)
}

function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'frost' : 'dark'
}

watch(theme, (t) => {
  applyTheme(t)
  try { localStorage.setItem(STORAGE_KEY, t) } catch {}
}, { immediate: true })

export function useTheme() {
  return { theme, toggleTheme }
}
