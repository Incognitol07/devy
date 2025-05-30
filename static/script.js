// filepath: c:\Users\femia\Desktop\Code\Projects\devspace\static\script.js
document.addEventListener("DOMContentLoaded", () => {
  const chatForm = document.getElementById("chat-form");
  const messageInput = document.getElementById("message-input");
  const chatMessages = document.getElementById("chat-messages");
  const assessmentResultsDiv = document.getElementById("assessment-results");
  const assessmentModal = document.getElementById("assessment-modal");
  const closeAssessmentBtn = document.getElementById("close-assessment");
  const newSessionBtn = document.getElementById("new-session-btn");

  // Close assessment modal when the close button is clicked
  closeAssessmentBtn.addEventListener("click", () => {
    assessmentModal.classList.remove("active");
    document.body.style.overflow = "auto"; // Re-enable scrolling
  });

  // Close modal when clicking outside the content area
  assessmentModal.addEventListener("click", (event) => {
    if (event.target === assessmentModal) {
      assessmentModal.classList.remove("active");
      document.body.style.overflow = "auto"; // Re-enable scrolling
    }
  });

  // New Session button functionality
  newSessionBtn.addEventListener("click", async () => {
    if (
      confirm(
        "Are you sure you want to start a new session? This will create a new conversation."
      )
    ) {
      try {
        const response = await fetch("/new-session", {
          method: "POST",
        });

        if (response.ok) {
          const data = await response.json();
          if (data.success) {
            window.location.href = "/"; // Reload the page with the new session
          } else {
            console.error("Failed to create new session:", data.message);
            alert("Failed to create new session. Please try again.");
          }
        } else {
          console.error("Error creating new session:", response.statusText);
          alert("Error creating new session. Please try again.");
        }
      } catch (error) {
        console.error("Failed to create new session:", error);
        alert(
          "Failed to create new session. Please check your connection and try again."
        );
      }
    }
  });

  function appendMessage(sender, text, isHTML = false) {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", sender.toLowerCase());

    const messageContent = document.createElement("div");
    messageContent.classList.add("message-content");

    if (isHTML) {
      messageContent.innerHTML = text;
    } else {
      const messageParagraph = document.createElement("p");
      messageParagraph.textContent = text;
      messageContent.appendChild(messageParagraph);
    }

    messageDiv.appendChild(messageContent);

    const timestampSpan = document.createElement("span");
    timestampSpan.classList.add("timestamp");

    const now = new Date();
    const formattedTime = now.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
    const formattedDate = now.toLocaleDateString([], {
      month: "short",
      day: "numeric",
      year: "numeric",
    });

    timestampSpan.textContent = `${formattedTime} · ${formattedDate}`;
    messageDiv.appendChild(timestampSpan);

    chatMessages.appendChild(messageDiv);
    scrollToBottom();
  }

  function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  scrollToBottom();

  function displayAssessment(payload) {
    assessmentResultsDiv.innerHTML = "";

    // User Summary
    if (payload.user_summary) {
      const userSummaryDiv = document.createElement("div");
      userSummaryDiv.classList.add("assessment-section");

      const userSummaryTitle = document.createElement("h4");
      userSummaryTitle.textContent = "Your Profile Summary";
      userSummaryDiv.appendChild(userSummaryTitle);

      const summaryList = document.createElement("ul");
      for (const [key, value] of Object.entries(payload.user_summary)) {
        if (key === "name") continue; // Skip displaying name as it's redundant

        const listItem = document.createElement("li");
        let displayValue = value;
        let formattedKey = key.replace(/_/g, " ");

        // Capitalize first letter of each word
        formattedKey = formattedKey
          .split(" ")
          .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
          .join(" ");

        if (Array.isArray(value)) {
          displayValue = value.join(", ") || "N/A";
        } else if (value === null || value === undefined || value === "") {
          displayValue = "N/A";
        }

        listItem.innerHTML = `<strong>${formattedKey}:</strong> ${displayValue}`;
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

        const recHeader = document.createElement("h5");
        recHeader.textContent = rec.career_name;

        // Add match score badge
        const matchScoreBadge = document.createElement("span");
        matchScoreBadge.classList.add("match-score");
        let score =
          rec.match_score !== undefined && rec.match_score !== null
            ? rec.match_score
            : "N/A";
        if (typeof score === "number") {
          matchScoreBadge.textContent = `${score}%`;
        } else {
          matchScoreBadge.textContent = score;
        }
        recHeader.appendChild(matchScoreBadge);

        recDiv.appendChild(recHeader);

        // Reasoning paragraph
        if (rec.reasoning) {
          const reasoningPara = document.createElement("p");
          reasoningPara.textContent = rec.reasoning;
          recDiv.appendChild(reasoningPara);
        }

        // Next steps section
        if (rec.suggested_next_steps && rec.suggested_next_steps.length > 0) {
          const nextStepsDiv = document.createElement("div");
          nextStepsDiv.classList.add("next-steps-list");

          const nextStepsTitle = document.createElement("h6");
          nextStepsTitle.textContent = "Suggested Next Steps";
          nextStepsDiv.appendChild(nextStepsTitle);

          const stepsList = document.createElement("ul");
          rec.suggested_next_steps.forEach((step) => {
            const stepItem = document.createElement("li");
            stepItem.textContent = step;
            stepsList.appendChild(stepItem);
          });

          nextStepsDiv.appendChild(stepsList);
          recDiv.appendChild(nextStepsDiv);
        }

        recommendationsDiv.appendChild(recDiv);
      });

      assessmentResultsDiv.appendChild(recommendationsDiv);
    }

    // Overall Assessment Notes
    if (payload.overall_assessment_notes) {
      const notesDiv = document.createElement("div");
      notesDiv.classList.add("assessment-notes");

      const notesTitle = document.createElement("h4");
      notesTitle.textContent = "Overall Assessment";
      notesDiv.appendChild(notesTitle);

      const notesParagraph = document.createElement("p");
      notesParagraph.textContent = payload.overall_assessment_notes;
      notesDiv.appendChild(notesParagraph);

      assessmentResultsDiv.appendChild(notesDiv);
    }

    // Show the modal with the assessment
    assessmentModal.classList.add("active");
    document.body.style.overflow = "hidden"; // Prevent background scrolling

    // Add a subtle entrance animation to each section
    const sections = assessmentResultsDiv.querySelectorAll(
      ".assessment-section, .assessment-notes"
    );
    sections.forEach((section, index) => {
      section.style.opacity = "0";
      section.style.transform = "translateY(20px)";
      section.style.transition = "opacity 0.5s ease, transform 0.5s ease";

      // Stagger the animations
      setTimeout(() => {
        section.style.opacity = "1";
        section.style.transform = "translateY(0)";
      }, 100 * (index + 1));
    });
  }

  chatForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const userMessage = messageInput.value.trim();

    if (userMessage) {
      appendMessage("user", userMessage);
      messageInput.value = "";
      messageInput.focus();

      // Show typing indicator
      const typingIndicator = document.createElement("div");
      typingIndicator.classList.add("message", "devy", "typing-indicator");
      typingIndicator.innerHTML =
        '<div class="typing-dots"><span></span><span></span><span></span></div>';
      chatMessages.appendChild(typingIndicator);
      scrollToBottom();

      const formData = new FormData();
      formData.append("user_message", userMessage);

      try {
        const response = await fetch("/chat", {
          method: "POST",
          body: formData,
        });

        // Remove typing indicator
        if (typingIndicator && typingIndicator.parentNode) {
          typingIndicator.parentNode.removeChild(typingIndicator);
        }

        if (!response.ok) {
          const errorData = await response
            .json()
            .catch(() => ({ detail: "Unknown error occurred" }));
          console.error("Error sending message:", response.status, errorData);
          appendMessage(
            "devy",
            `Sorry, I'm having trouble processing your request. Please try again in a moment. (Error: ${
              errorData.detail || response.statusText
            })`
          );
          return;
        }

        const data = await response.json();

        if (data.is_assessment_complete && data.recommendation_payload) {
          // Display the assessment in the modal
          displayAssessment(data.recommendation_payload);

          // Also add a message in the chat to indicate assessment is ready
          appendMessage("devy", data.devy_response);

          // Add a button to view the assessment again if needed
          addViewAssessmentButton();
        } else if (data.devy_response) {
          // Regular message
          appendMessage("devy", data.devy_response);
        }
      } catch (error) {
        console.error("Failed to send message:", error);
        appendMessage(
          "devy",
          "Sorry, I encountered a problem trying to respond. Please check your connection and try again."
        );
      }
    }
  });

  // Add CSS for typing indicator
  const style = document.createElement("style");
  style.textContent = `
    .typing-indicator {
      padding: 12px 20px;
    }
    .typing-dots {
      display: flex;
      align-items: center;
      height: 24px;
    }
    .typing-dots span {
      height: 8px;
      width: 8px;
      margin: 0 2px;
      background-color: var(--devy-medium-gray);
      border-radius: 50%;
      display: inline-block;
      opacity: 0.7;
      animation: typing-dot 1.4s infinite ease-in-out both;
    }
    .typing-dots span:nth-child(1) {
      animation-delay: 0s;
    }
    .typing-dots span:nth-child(2) {
      animation-delay: 0.2s;
    }
    .typing-dots span:nth-child(3) {
      animation-delay: 0.4s;
    }
    @keyframes typing-dot {
      0%, 80%, 100% { transform: scale(0.7); }
      40% { transform: scale(1.2); }
    }
  `;
  document.head.appendChild(style);

  // Focus on the input field initially
  messageInput.focus();

  // Add a "View Assessment" button in chat when assessment is available
  function addViewAssessmentButton() {
    const viewButtonContainer = document.createElement("div");
    viewButtonContainer.classList.add("view-assessment-container");

    const viewButton = document.createElement("button");
    viewButton.textContent = "View Your Career Assessment";
    viewButton.classList.add("view-assessment-button");
    viewButton.addEventListener("click", () => {
      assessmentModal.classList.add("active");
      document.body.style.overflow = "hidden";
    });

    viewButtonContainer.appendChild(viewButton);
    chatMessages.appendChild(viewButtonContainer);
    scrollToBottom();
  }
  // Handle initial message display from template
  if (typeof initialDevyTimestamp !== "undefined" && initialDevyTimestamp) {
    // The initial message is already in the HTML, so we just ensure it's visible
    scrollToBottom();
  }

  // Check for and display existing assessment
  if (
    typeof hasExistingAssessment !== "undefined" &&
    hasExistingAssessment &&
    existingAssessmentData
  ) {
    // Display the assessment modal with the existing data
    displayAssessment(existingAssessmentData);

    // Also add the "View Assessment" button to the chat
    addViewAssessmentButton();
  }
});

// Add keyboard event for ESC key to close modal
document.addEventListener("keydown", function (event) {
  const assessmentModal = document.getElementById("assessment-modal");
  if (event.key === "Escape" && assessmentModal.classList.contains("active")) {
    assessmentModal.classList.remove("active");
    document.body.style.overflow = "auto"; // Re-enable scrolling
  }
});

function formatKey(key) {
  return key
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}
