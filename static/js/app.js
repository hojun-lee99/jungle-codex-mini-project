$(function () {
    $(document).on("click", ".quiz-vote-btn", function () {
        const button = $(this);
        const quizId = button.data("quiz-id");
        const choice = button.data("choice");

        button.closest(".quiz-card").find(".quiz-vote-btn").prop("disabled", true);

        $.ajax({
            url: "/quiz/vote",
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify({ quiz_id: quizId, choice: choice }),
        })
            .done(function (response) {
                const result = response.result;
                const container = $(`[data-quiz-result='${quizId}']`);
                container.html(`
                    <div class="quiz-result-labels">
                        <span>${result.left_label} ${result.left_rate}%</span>
                        <span>${result.right_label} ${result.right_rate}%</span>
                    </div>
                    <div class="progress rounded-pill" style="height: 12px;">
                        <div class="progress-bar bg-dark" role="progressbar" style="width: ${result.left_rate}%"></div>
                        <div class="progress-bar bg-warning" role="progressbar" style="width: ${result.right_rate}%"></div>
                    </div>
                    <p class="text-muted small mt-3 mb-0">누적 투표 ${result.left_votes + result.right_votes}건</p>
                `);
            })
            .fail(function () {
                alert("투표 처리 중 문제가 발생했습니다.");
            })
            .always(function () {
                button.closest(".quiz-card").find(".quiz-vote-btn").prop("disabled", false);
            });
    });
});
