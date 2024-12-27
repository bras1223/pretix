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
      clearTimeoutRef: null, // Reference to the timeout
    };
  },
  methods: {
    startScanner() {
      if (!window.Html5Qrcode) {
        console.error("Html5Qrcode library is not loaded.");
        return;
      }

      const config = { fps: 10, qrbox: 250 };
      this.qrCodeScanner = new window.Html5Qrcode("reader");

      this.qrCodeScanner.start(
          { facingMode: "environment" }, // Use back camera
          config,
          (decodedText) => {
            // Prevent duplicate consecutive scans
            if (decodedText !== this.lastScannedCode) {
              this.lastScannedCode = decodedText;

              // Emit scanned result to parent component
              this.$emit("qr-scanned", decodedText);

              // Clear previous timeout
              if (this.clearTimeoutRef) {
                clearTimeout(this.clearTimeoutRef);
              }

              // Reset lastScannedCode after 2 seconds to allow re-scanning
              this.clearTimeoutRef = setTimeout(() => {
                this.lastScannedCode = null;
              }, 4000);
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
    if (this.clearTimeoutRef) {
      clearTimeout(this.clearTimeoutRef); // Clean up timeout on component destroy
    }
  },
};
</script>