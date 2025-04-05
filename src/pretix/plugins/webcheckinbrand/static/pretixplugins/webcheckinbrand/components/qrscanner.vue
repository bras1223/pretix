<template>
  <div> <!-- single root -->
    <div v-if="confirmVisible" class="confirm-overlay">
      <div class="confirm-dialog">
        <p class="confirm-text">Je hebt deze kaart zojuist al gescand. Wil je hem opnieuw scannen?</p>
        <div class="confirm-actions">
          <button class="btn btn-confirm" @click="onConfirm(true)">Ja</button>
          <button class="btn btn-cancel" @click="onConfirm(false)">Nee</button>
        </div>
      </div>
    </div>
  <div id="qr-scanner">
    <div id="reader" style="width: 100%"></div>
  </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      qrCodeScanner: null,
      confirmVisible: false,
      pendingDecodedText: null,
      lastScannedCode: null, // Cache to prevent consecutive duplicates
      lastScannedTime: null, // Track the time of the last scan
    };
  },
  methods: {
    startScanner() {
      if (!window.Html5Qrcode) {
        console.error("Html5Qrcode library is not loaded.");
        return;
      }

      let qrboxFunction = function(viewfinderWidth, viewfinderHeight) {
        let minEdgePercentage = 0.7; // 70%
        let minEdgeSize = Math.min(viewfinderWidth, viewfinderHeight);
        let qrboxSize = Math.floor(minEdgeSize * minEdgePercentage);
        return {
          width: qrboxSize,
          height: qrboxSize
        };
      }

      const config = { fps: 10, qrbox: qrboxFunction, videoConstraints: {
          aspectRatio: 1.0,  facingMode: {
            exact: "environment"
          }
        }, showTorchButtonIfSupported: true};
      this.qrCodeScanner = new window.Html5Qrcode("reader");

      this.qrCodeScanner.start(
          { facingMode: "environment" }, // Use back camera
          config,
          (decodedText) => {
            const now = Date.now();

            const isDuplicate = decodedText === this.lastScannedCode;
            const isWithinFourSeconds = this.lastScannedTime && (now - this.lastScannedTime) < 6000;

            if ((isDuplicate && isWithinFourSeconds) || decodedText === this.pendingDecodedText) {
              return;
            }

            if (isDuplicate && !isWithinFourSeconds) {
              if (isDuplicate && !isWithinFourSeconds) {
                this.pendingDecodedText = decodedText;
                this.confirmVisible = true; // Show custom confirm modal
              }
            } else {
              // If different code or enough time has passed, process it
              this.lastScannedCode = decodedText;
              this.lastScannedTime = Date.now(); // Update the scan time

              // Emit scanned result to parent component
              this.$emit("qr-scanned", decodedText);
            }
          },
          (error) => {

          }
      );
    },
    onConfirm(confirmed) {
      if (confirmed && this.pendingDecodedText) {
        this.lastScannedCode = this.pendingDecodedText;
        this.lastScannedTime = Date.now();
        this.$emit("qr-scanned", this.pendingDecodedText);
      }
      // Reset confirmation state
      this.pendingDecodedText = null;
      this.confirmVisible = false;
    },
  },
  mounted() {
    this.startScanner();
  },
  beforeDestroy() {
    if (this.qrCodeScanner) {
      this.qrCodeScanner.stop();
    }
  },
};
</script>