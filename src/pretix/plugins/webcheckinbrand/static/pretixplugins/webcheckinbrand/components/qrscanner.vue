<template>
  <div id="qr-scanner">
    <div id="reader" style="width: 100%"></div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      qrCodeScanner: null,
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
            if (decodedText === this.lastScannedCode && this.lastScannedTime && Date.now() - this.lastScannedTime < 4000) {
              // Ignore scans within 4 seconds (duplicate scan)
              return;
            } else if (decodedText === this.lastScannedCode && Date.now() - this.lastScannedTime >= 4000) {
              // Same code but after 4 seconds
              const userConfirmed = window.confirm("Je hebt deze kaart zojuist al gescand. Wil je hem opnieuw scannen?");
              if (userConfirmed) {
                // Emit scanned result to parent component
                this.$emit("qr-scanned", decodedText);
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