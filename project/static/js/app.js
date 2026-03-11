document.addEventListener("DOMContentLoaded", () => {
    const fileInput = document.querySelector("#document");
    const previewPanel = document.querySelector("#upload-preview");

    if (!fileInput || !previewPanel) {
        return;
    }

    fileInput.addEventListener("change", () => {
        const file = fileInput.files?.[0];
        if (!file) {
            previewPanel.innerHTML = '<div class="preview-empty">선택한 파일의 미리보기가 여기에 표시됩니다.</div>';
            return;
        }

        const objectUrl = URL.createObjectURL(file);
        if (file.type.startsWith("image/")) {
            previewPanel.innerHTML = `<img src="${objectUrl}" alt="업로드 미리보기">`;
            return;
        }

        if (file.type === "application/pdf") {
            previewPanel.innerHTML = `<iframe src="${objectUrl}" title="PDF 미리보기"></iframe>`;
            return;
        }

        previewPanel.innerHTML = '<div class="preview-empty">이 파일 형식은 브라우저 미리보기를 지원하지 않습니다.</div>';
    });
});

