// Crisis.js - Emergency protocols

document.addEventListener("DOMContentLoaded", function () {
	// Add event listeners to call buttons
	const callButtons = document.querySelectorAll('a[href^="tel:"]');
	callButtons.forEach((button) => {
		button.addEventListener("click", function (e) {
			// Optional: Track emergency calls or show confirmation
			console.log("Emergency call initiated to:", this.href);
		});
	});

	// Optional: Add shake detection for emergency (if supported)
	if (window.DeviceMotionEvent) {
		let shakeCount = 0;
		const shakeThreshold = 15;
		let lastShake = Date.now();

		window.addEventListener("devicemotion", function (event) {
			const acceleration = event.accelerationIncludingGravity;
			const now = Date.now();

			if (now - lastShake > 100) {
				const totalAcceleration =
					Math.abs(acceleration.x) +
					Math.abs(acceleration.y) +
					Math.abs(acceleration.z);
				if (totalAcceleration > shakeThreshold) {
					shakeCount++;
					if (shakeCount > 5) {
						// Trigger emergency
						alert("Emergency shake detected! Calling helpline...");
						// In a real app, auto-call helpline
						shakeCount = 0;
					}
				}
				lastShake = now;
			}
		});
	}
});
