document.addEventListener("DOMContentLoaded", function () {
	const messageInput = document.getElementById("messageInput");
	const sendButton = document.getElementById("sendButton");
	const chatMessages = document.getElementById("chatMessages");
	const languageSelect = document.getElementById("languageSelect");

	sendButton.addEventListener("click", sendMessage);
	messageInput.addEventListener("keypress", function (e) {
		if (e.key === "Enter" && !e.shiftKey) {
			e.preventDefault();
			sendMessage();
		}
	});

	function sendMessage() {
		const message = messageInput.value.trim();
		if (!message) return;

		const language = languageSelect.value;

		// Add user message to chat
		addMessage("user", message);

		// Clear input
		messageInput.value = "";

		// Send to server
		fetch("/api/chat", {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify({ message: message, language: language }),
		})
			.then((response) => response.json())
			.then((data) => {
				addMessage("ai", data.response);
				if (data.crisis) {
					alert(
						"Crisis detected. Please seek immediate help from the emergency resources."
					);
				}
			})
			.catch((error) => {
				console.error("Error:", error);
				addMessage(
					"ai",
					"Sorry, there was an error processing your message. Please try again."
				);
			});
	}

	function addMessage(sender, text) {
		const messageDiv = document.createElement("div");
		messageDiv.className = `message ${sender}-message`;
		messageDiv.textContent = text;
		messageDiv.style.opacity = "0";
		messageDiv.style.transform = "translateY(20px)";
		chatMessages.appendChild(messageDiv);

		// Animate in
		setTimeout(() => {
			messageDiv.style.transition = "opacity 0.5s ease, transform 0.5s ease";
			messageDiv.style.opacity = "1";
			messageDiv.style.transform = "translateY(0)";
		}, 10);

		// Smooth scroll
		setTimeout(() => {
			chatMessages.scrollTo({
				top: chatMessages.scrollHeight,
				behavior: "smooth",
			});
		}, 100);
	}
});
