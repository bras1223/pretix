import { createApp } from 'vue'

import App from './components/app.vue'

const mountEl = document.querySelector<HTMLElement>('#app')!

const app = createApp(App, mountEl.dataset)
app.mount('#app')

app.config.errorHandler = (error, _vm, info) => {
	console.error('[VUE]', info, error)
}
