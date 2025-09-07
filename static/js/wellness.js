document.addEventListener("DOMContentLoaded", function () {
	const moodForm = document.getElementById("moodForm");
	const moodSlider = document.getElementById("moodSlider");
	const moodValue = document.getElementById("moodValue");

	// Update mood value display
	moodSlider.addEventListener("input", function () {
		moodValue.textContent = moodSlider.value;
	});

	// Handle form submission
	moodForm.addEventListener("submit", function (e) {
		e.preventDefault();
		const mood = parseInt(moodSlider.value);

		fetch("/api/mood", {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify({ mood: mood }),
		})
			.then((response) => response.json())
			.then((data) => {
				if (data.success) {
					alert("Mood logged successfully!");
					// Optionally, update the chart
					location.reload();
				} else {
					alert("Error logging mood. Please try again.");
				}
			})
			.catch((error) => {
				console.error("Error:", error);
				alert("Error logging mood. Please try again.");
			});
	});

	// Initialize chart if moodHistory is available
	if (typeof moodHistory !== "undefined" && moodHistory.length > 0) {
		const ctx = document.getElementById("moodChart").getContext("2d");
		const labels = moodHistory.map((entry) =>
			new Date(entry.date).toLocaleDateString()
		);
		const data = moodHistory.map((entry) => entry.mood);

		new Chart(ctx, {
			type: "line",
			data: {
				labels: labels,
				datasets: [
					{
						label: "Mood",
						data: data,
						borderColor: "rgb(75, 192, 192)",
						tension: 0.1,
					},
				],
			},
			options: {
				responsive: true,
				scales: {
					y: {
						beginAtZero: true,
						max: 10,
					},
				},
			},
		});
	}
});
