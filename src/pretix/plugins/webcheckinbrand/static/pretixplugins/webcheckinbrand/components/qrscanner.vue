<template>
  <div>
    <div v-if="confirmVisible" class="confirm-overlay" @click.self="onConfirm(false)">
      <div class="confirm-dialog" role="dialog" aria-modal="true">
        <p class="confirm-text">{{ confirmText }}</p>
        <div class="confirm-actions">
          <button type="button" class="btn btn-confirm" @click="onConfirm(true)">{{ yesText }}</button>
          <button type="button" class="btn btn-cancel" @click="onConfirm(false)">{{ noText }}</button>
        </div>
      </div>
    </div>
    <div id="qr-scanner">
      <div id="reader" style="width: 100%"></div>
    </div>
  </div>
</template>

<script>
import { STRINGS } from '../i18n'

// Treat the same code as still "in view" if we see it again within this window.
const PRESENT_MS = 1500

export default {
  data() {
    return {
      qrCodeScanner: null,
      confirmVisible: false,
      pendingDecodedText: null,
      lastEmittedCode: null,
      lastSeenCode: null,
      lastSeenAt: null,
      confirmText: STRINGS['scan.duplicate'],
      yesText: STRINGS['yes'],
      noText: STRINGS['no'],
    }
  },
  methods: {
    startScanner() {
      if (!window.Html5Qrcode) {
        console.error('Html5Qrcode library is not loaded.')
        return
      }

      const qrboxFunction = function (viewfinderWidth, viewfinderHeight) {
        const minEdgePercentage = 0.7
        const minEdgeSize = Math.min(viewfinderWidth, viewfinderHeight)
        const qrboxSize = Math.floor(minEdgeSize * minEdgePercentage)
        return {
          width: qrboxSize,
          height: qrboxSize,
        }
      }

      const config = {
        fps: 10,
        qrbox: qrboxFunction,
        aspectRatio: 1.333334,
        showTorchButtonIfSupported: true,
      }
      this.qrCodeScanner = new window.Html5Qrcode('reader')

      const onScan = (decodedText) => {
        const now = Date.now()

        if (this.confirmVisible) {
          return
        }

        const stillPresent =
          decodedText === this.lastSeenCode &&
          this.lastSeenAt &&
          now - this.lastSeenAt < PRESENT_MS

        this.lastSeenCode = decodedText
        this.lastSeenAt = now

        if (stillPresent) {
          return
        }

        // Code (re)appeared after leaving the view.
        if (decodedText === this.lastEmittedCode) {
          this.pendingDecodedText = decodedText
          this.confirmVisible = true
          return
        }

        this.emitScan(decodedText)
      }

      const cameraConfigs = [
        { facingMode: 'environment' },
        { facingMode: 'user' },
        true,
      ]

      const tryStart = (index) => {
        if (index >= cameraConfigs.length) {
          console.error('Could not start QR scanner: no suitable camera found.')
          return
        }
        this.qrCodeScanner
          .start(cameraConfigs[index], config, onScan, () => {})
          .catch(() => tryStart(index + 1))
      }

      tryStart(0)
    },
    emitScan(decodedText) {
      this.lastEmittedCode = decodedText
      this.lastSeenCode = decodedText
      this.lastSeenAt = Date.now()
      this.$emit('qr-scanned', decodedText)
    },
    onConfirm(confirmed) {
      const code = this.pendingDecodedText
      this.pendingDecodedText = null
      this.confirmVisible = false

      if (confirmed && code) {
        this.emitScan(code)
        return
      }

      // Declined: keep treating this code as already handled until it leaves the view.
      if (code) {
        this.lastEmittedCode = code
        this.lastSeenCode = code
        this.lastSeenAt = Date.now()
      }
    },
  },
  mounted() {
    this.startScanner()
  },
  beforeUnmount() {
    if (this.qrCodeScanner) {
      this.qrCodeScanner.stop().catch(() => {})
    }
  },
  beforeDestroy() {
    if (this.qrCodeScanner) {
      this.qrCodeScanner.stop().catch(() => {})
    }
  },
}
</script>
