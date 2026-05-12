document.addEventListener("visibilitychange", function () {
    if (document.hidden) {
        fetch("/api/suspicious-activity", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                type: "TAB_SWITCH",
                module: window.location.pathname
            })
        });
    }
});