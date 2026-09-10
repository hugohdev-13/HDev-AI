document.addEventListener("DOMContentLoaded", () => {
    const assistant = document.getElementById("editorial-assistant");
    if (!assistant) {
        return;
    }

    const generateButton = document.getElementById("generate-editorial-suggestions");
    const results = document.getElementById("editorial-suggestions-results");
    const errorBox = document.getElementById("editorial-suggestions-error");
    let suggestions = null;

    const showError = (message) => {
        errorBox.textContent = message;
        errorBox.classList.remove("d-none");
    };

    const setOutput = (name, value) => {
        const output = assistant.querySelector(`[data-suggestion-output="${name}"]`);
        if (output) {
            output.textContent = Array.isArray(value) ? value.join(", ") : value || "—";
        }
    };

    generateButton.addEventListener("click", async () => {
        generateButton.disabled = true;
        errorBox.classList.add("d-none");
        try {
            const response = await fetch(assistant.dataset.suggestionsUrl, {
                method: "POST",
                headers: {
                    "Accept": "application/json",
                    "X-CSRFToken": window.HDevAI?.getCsrfToken?.() || "",
                    "X-Requested-With": "XMLHttpRequest",
                },
                credentials: "same-origin",
            });
            const payload = await response.json();
            if (!response.ok || payload.suggestions?.status !== "completed") {
                throw new Error(payload.suggestions?.error || payload.message || "No fue posible generar sugerencias.");
            }
            suggestions = payload.suggestions;
            ["suggested_title", "suggested_summary", "suggested_content", "suggested_category", "keywords"].forEach(
                (field) => setOutput(field, suggestions[field])
            );
            results.classList.remove("d-none");
        } catch (error) {
            showError(error.message || "No fue posible generar sugerencias.");
        } finally {
            generateButton.disabled = false;
        }
    });

    assistant.querySelectorAll("[data-apply-suggestion]").forEach((button) => {
        button.addEventListener("click", () => {
            if (!suggestions) {
                return;
            }
            const fieldId = button.dataset.applySuggestion;
            if (fieldId === "category_id") {
                const matchingOption = Array.from(document.querySelectorAll("#category_id option"))
                    .find((option) => option.textContent.trim() === suggestions.suggested_category);
                if (!matchingOption) {
                    showError("La categoría sugerida no está disponible entre las categorías activas.");
                    return;
                }
                matchingOption.selected = true;
                return;
            }
            const field = document.getElementById(fieldId);
            const suggestionName = `suggested_${fieldId}`;
            if (field && suggestions[suggestionName]) {
                field.value = suggestions[suggestionName];
                field.dispatchEvent(new Event("input", { bubbles: true }));
            }
        });
    });

    assistant.querySelectorAll("[data-copy-suggestion]").forEach((button) => {
        button.addEventListener("click", async () => {
            const value = suggestions?.[button.dataset.copySuggestion];
            if (!Array.isArray(value) || !value.length) {
                return;
            }
            try {
                await navigator.clipboard.writeText(value.join(", "));
                button.textContent = "Copiadas";
            } catch (_error) {
                showError("No fue posible copiar las keywords.");
            }
        });
    });
});
