window.HDevAI = window.HDevAI || {};
window.HDevAI.getCsrfToken = () => (
    document.querySelector('meta[name="csrf-token"]')?.getAttribute("content") || ""
);

document.addEventListener("DOMContentLoaded", () => {
    const csrfToken = window.HDevAI.getCsrfToken();
    document.querySelectorAll('form[method="post" i]').forEach((form) => {
        if (!csrfToken || form.querySelector('input[name="csrf_token"]')) {
            return;
        }
        const tokenInput = document.createElement("input");
        tokenInput.type = "hidden";
        tokenInput.name = "csrf_token";
        tokenInput.value = csrfToken;
        form.prepend(tokenInput);
    });

    document.querySelectorAll(".app-alert").forEach((alert) => {
        window.setTimeout(() => bootstrap.Alert.getOrCreateInstance(alert).close(), 5000);
    });
});
