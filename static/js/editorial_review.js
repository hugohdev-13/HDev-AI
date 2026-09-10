(() => {
    "use strict";

    const reviewContainer = document.getElementById("editorial-review");
    if (!reviewContainer) {
        return;
    }

    const button = document.getElementById("generate-editorial-review");
    const errorElement = document.getElementById("editorial-review-error");
    const resultsElement = document.getElementById("editorial-review-results");
    const readinessLabels = {
        ready: "Listo",
        needs_review: "Requiere revisión",
        not_ready: "No listo",
    };
    const riskLabels = {low: "Bajo", medium: "Medio", high: "Alto"};

    const showError = (message) => {
        errorElement.textContent = message;
        errorElement.classList.remove("d-none");
    };

    const renderList = (field, values) => {
        const list = reviewContainer.querySelector(`[data-review-list="${field}"]`);
        list.replaceChildren();
        const items = Array.isArray(values) && values.length ? values : ["Sin observaciones."];
        items.forEach((item) => {
            const listItem = document.createElement("li");
            listItem.textContent = item;
            list.appendChild(listItem);
        });
    };

    const renderReview = (review) => {
        reviewContainer.querySelectorAll("[data-review-score]").forEach((element) => {
            element.textContent = String(review[element.dataset.reviewScore] ?? 0);
        });
        reviewContainer.querySelector("[data-review-readiness]").textContent =
            readinessLabels[review.publication_readiness] || "Requiere revisión";
        reviewContainer.querySelector("[data-review-risk]").textContent =
            riskLabels[review.factual_risk_level] || "Medio";
        ["strengths", "issues", "recommendations", "missing_information"].forEach(
            (field) => renderList(field, review[field]),
        );
        resultsElement.classList.remove("d-none");
    };

    button.addEventListener("click", async () => {
        errorElement.classList.add("d-none");
        button.disabled = true;
        const originalText = button.textContent;
        button.textContent = "Revisando…";
        try {
            const response = await fetch(reviewContainer.dataset.reviewUrl, {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    Accept: "application/json",
                    "X-CSRFToken": window.HDevAI?.getCsrfToken?.() || "",
                },
            });
            const payload = await response.json();
            if (!response.ok || !payload.review || payload.review.status === "failed") {
                throw new Error(
                    payload.review?.error || payload.message ||
                    "No fue posible completar la revisión editorial.",
                );
            }
            renderReview(payload.review);
        } catch (error) {
            showError(error.message || "No fue posible completar la revisión editorial.");
        } finally {
            button.disabled = false;
            button.textContent = originalText;
        }
    });
})();
