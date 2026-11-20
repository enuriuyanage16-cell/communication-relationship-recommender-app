// Shared code for the test pages: checks answers and moves between pages
(function () {
    var form = document.querySelector("[data-test-form]");
    if (!form) return;
    form.noValidate = true;
    var steps = form.querySelectorAll("[data-step]");
    var current = 1;

    function unanswered(container) {
        var missing = [];
        container.querySelectorAll("[data-question]").forEach(function (question) {
            var answered = question.querySelector("input:checked");
            question.classList.toggle("is-missing", !answered);
            if (!answered) missing.push(question);
        });
        return missing;
    }

    function check(container) {
        var missing = unanswered(container);
        if (missing.length) {
            missing[0].scrollIntoView({ behavior: "smooth", block: "center" });
            return false;
        }
        return true;
    }

    form.addEventListener("change", function (event) {
        var question = event.target.closest("[data-question]");
        if (question) question.classList.remove("is-missing");
    });

    if (!steps.length) {
        form.addEventListener("submit", function (event) {
            if (!check(form)) event.preventDefault();
        });
        return;
    }

    var back = form.querySelector("[data-back]");
    var next = form.querySelector("[data-next]");
    var submit = form.querySelector("[data-submit]");
    var label = document.querySelector("[data-step-label]");
    var bar = document.querySelector("[data-step-bar]");

    function show(step) {
        current = step;
        steps.forEach(function (s) { s.hidden = Number(s.dataset.step) !== step; });
        back.hidden = step === 1;
        next.hidden = step === steps.length;
        submit.hidden = step !== steps.length;
        label.textContent = "Page " + step + " of " + steps.length;
        bar.style.width = ((step - 1) / steps.length * 100) + "%";
        window.scrollTo({ top: 0, behavior: "smooth" });
    }

    next.addEventListener("click", function () {
        if (check(steps[current - 1])) show(current + 1);
    });
    back.addEventListener("click", function () { show(current - 1); });
    form.addEventListener("submit", function (event) {
        if (!check(form)) {
            event.preventDefault();
            var first = form.querySelector(".is-missing");
            var step = Number(first.closest("[data-step]").dataset.step);
            if (step !== current) show(step);
            first.scrollIntoView({ behavior: "smooth", block: "center" });
        }
    });
    show(1);
})();
