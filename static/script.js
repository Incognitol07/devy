// filepath: c:\Users\femia\Desktop\Code\Projects\devspace\static\script.js
document.addEventListener("DOMContentLoaded", () => {
  const chatForm = document.getElementById("chat-form");
  const messageInput = document.getElementById("message-input");
  const chatMessages = document.getElementById("chat-messages");
  const assessmentResultsDiv = document.getElementById("assessment-results"); // Added

  // currentSessionId is passed from the template
  // console.log("Current Session ID:", currentSessionId);

  function appendMessage(sender, text, isHTML = false) {
    // Added isHTML parameter
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", sender.toLowerCase());

    if (isHTML) {
      messageDiv.innerHTML = text; // Use innerHTML if text is HTML
    } else {
      const messageParagraph = document.createElement("p");
      messageParagraph.textContent = text;
      messageDiv.appendChild(messageParagraph);
    }

    // Timestamp logic can remain the same if you want timestamps for assessment block
    // Or you can conditionally add it. For simplicity, keeping it for now.
    const timestampSpan = document.createElement("span");
    timestampSpan.classList.add("timestamp");
    timestampSpan.textContent =
      new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }) +
      " - " +
      new Date().toLocaleDateString();
    messageDiv.appendChild(timestampSpan);

    chatMessages.appendChild(messageDiv);
    scrollToBottom();
  }

  function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  // Initial scroll to bottom if there are pre-loaded messages
  scrollToBottom();

  function displayAssessment(payload) {
    assessmentResultsDiv.innerHTML = ""; // Clear previous results if any

    const title = document.createElement("h3");
    title.textContent = "Career Assessment Results";
    assessmentResultsDiv.appendChild(title);

    // User Summary
    if (payload.user_summary) {
      const userSummaryDiv = document.createElement("div");
      userSummaryDiv.classList.add("assessment-section");
      const userSummaryTitle = document.createElement("h4");
      userSummaryTitle.textContent = "User Profile Summary";
      userSummaryDiv.appendChild(userSummaryTitle);

      const summaryList = document.createElement("ul");
      for (const [key, value] of Object.entries(payload.user_summary)) {
        const listItem = document.createElement("li");
        let displayValue = value;
        if (Array.isArray(value)) {
          displayValue = value.join(", ") || "N/A";
        } else if (value === null || value === undefined || value === "") {
          displayValue = "N/A";
        }
        listItem.innerHTML = `<strong>${key
          .replace(/_/g, " ")
          .replace(/\\b\\w/g, (l) =>
            l.toUpperCase()
          )}:</strong> ${displayValue}`;
        summaryList.appendChild(listItem);
      }
      userSummaryDiv.appendChild(summaryList);
      assessmentResultsDiv.appendChild(userSummaryDiv);
    }

    // Career Recommendations
    if (
      payload.career_recommendations &&
      payload.career_recommendations.length > 0
    ) {
      const recommendationsDiv = document.createElement("div");
      recommendationsDiv.classList.add("assessment-section");
      const recommendationsTitle = document.createElement("h4");
      recommendationsTitle.textContent = "Career Recommendations";
      recommendationsDiv.appendChild(recommendationsTitle);

      payload.career_recommendations.forEach((rec) => {
        const recDiv = document.createElement("div");
        recDiv.classList.add("recommendation-item");

        const recName = document.createElement("h5");
        recName.textContent = rec.career_name;
        recDiv.appendChild(recName);

        const recDetailsList = document.createElement("ul");
        let score =
          rec.match_score !== undefined && rec.match_score !== null
            ? rec.match_score
            : "N/A";
        if (typeof score === "number") score = `${score}%`;

        recDetailsList.innerHTML = `
          <li><strong>Match Score:</strong> ${score}</li>
          <li><strong>Reasoning:</strong> ${rec.reasoning || "N/A"}</li>
          <li><strong>Suggested Next Steps:</strong> 
            <ul>${
              (rec.suggested_next_steps || [])
                .map((step) => `<li>${step}</li>`)
                .join("") || "<li>N/A</li>"
            }</ul>
          </li>
        `;
        recDiv.appendChild(recDetailsList);
        recommendationsDiv.appendChild(recDiv);
      });
      assessmentResultsDiv.appendChild(recommendationsDiv);
    }

    // Overall Assessment Notes
    if (payload.overall_assessment_notes) {
      const notesDiv = document.createElement("div");
      notesDiv.classList.add("assessment-section");
      const notesTitle = document.createElement("h4");
      notesTitle.textContent = "Overall Assessment Notes";
      notesDiv.appendChild(notesTitle);
      const notesParagraph = document.createElement("p");
      notesParagraph.textContent = payload.overall_assessment_notes;
      notesDiv.appendChild(notesParagraph);
      assessmentResultsDiv.appendChild(notesDiv);
    }

    // Disable chat input
    messageInput.disabled = true;
    messageInput.placeholder =
      "Assessment complete. Refresh to start a new session.";
    chatForm.querySelector("button[type='submit']").disabled = true;

    scrollToBottom(); // Scroll to show the assessment
  }

  chatForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const userMessage = messageInput.value.trim();

    if (userMessage) {
      appendMessage("user", userMessage);
      messageInput.value = "";

      const formData = new FormData();
      formData.append("user_message", userMessage);

      try {
        const response = await fetch("/chat", {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          const errorData = await response
            .json()
            .catch(() => ({ detail: "Unknown error occurred" }));
          console.error("Error sending message:", response.status, errorData);
          appendMessage(
            "devy",
            `Error: ${errorData.detail || response.statusText}`
          );
          return;
        }

        const data = await response.json();

        if (data.devy_response && !data.is_assessment_complete) {
          // Only append if not assessment message
          appendMessage("devy", data.devy_response);
        }

        if (data.is_assessment_complete && data.recommendation_payload) {
          appendMessage("devy", data.devy_response); // Append the introductory message for assessment
          displayAssessment(data.recommendation_payload);
        }
      } catch (error) {
        console.error("Failed to send message:", error);
        appendMessage(
          "devy",
          "Sorry, I encountered a problem trying to respond."
        );
      }
    }
  });

  // Focus on the input field initially
  messageInput.focus();

  // Initial greeting from Devy if any (passed from template)
  // This part might need adjustment based on how initial_devy_message is handled
  // For now, assuming it's a simple string.
  if (typeof initialDevyMessage !== "undefined" && initialDevyMessage) {
    appendMessage("devy", initialDevyMessage);
  }
  if (typeof initialDevyTimestamp !== "undefined" && initialDevyTimestamp) {
    // If you want to display the initial message with its server-generated timestamp
    // you'll need to adjust appendMessage or have a dedicated function.
    // For now, the client-side timestamp is used by appendMessage.
  }

  scrollToBottom(); // Ensure scroll after initial message
});
