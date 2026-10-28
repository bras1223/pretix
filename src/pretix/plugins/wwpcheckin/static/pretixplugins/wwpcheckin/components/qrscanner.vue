<script setup>
import { onMounted, onBeforeUnmount, ref } from 'vue'

const emit = defineEmits(['qr-scanned'])

const qrCodeScanner = ref(null)
let lastScannedCode = null
let clearTimeoutRef = null

function startScanner () {
	if (!window.Html5Qrcode) {
		console.error('Html5Qrcode library is not loaded.')
		return
	}

	const config = { fps: 10, qrbox: 250, aspectRatio: 1.333334 }
	qrCodeScanner.value = new window.Html5Qrcode('reader')

	qrCodeScanner.value.start(
		{ facingMode: 'environment' },
		config,
		(decodedText) => {
			if (decodedText !== lastScannedCode) {
				lastScannedCode = decodedText
				emit('qr-scanned', decodedText)
				if (clearTimeoutRef) {
					clearTimeout(clearTimeoutRef)
				}
				clearTimeoutRef = setTimeout(() => {
					lastScannedCode = null
				}, 4000)
			}
		},
		() => {}
	)
}

onMounted(() => {
	startScanner()
})

onBeforeUnmount(() => {
	if (qrCodeScanner.value) {
		qrCodeScanner.value.stop().catch(() => {})
	}
	if (clearTimeoutRef) {
		clearTimeout(clearTimeoutRef)
	}
})
</script>

<template>
	<div id="qr-scanner">
		<div id="reader" style="width: 100%"></div>
	</div>
</template>
