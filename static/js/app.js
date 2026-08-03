document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".app-alert").forEach((alert) => {
        window.setTimeout(() => bootstrap.Alert.getOrCreateInstance(alert).close(), 5000);
    });
});
