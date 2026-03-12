from io import BytesIO
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas


def render_exam_pdf(title: str, questions: list[dict]) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=LETTER)

    width, height = LETTER
    y = height - 72

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(72, y, title)
    y -= 36

    pdf.setFont("Helvetica", 12)
    for idx, q in enumerate(questions, start=1):
        if y < 100:
            pdf.showPage()
            y = height - 72
            pdf.setFont("Helvetica", 12)

        pdf.drawString(72, y, f"{idx}. {q['question']}")
        y -= 18

        for key, val in q.get("options", {}).items():
            if y < 100:
                pdf.showPage()
                y = height - 72
                pdf.setFont("Helvetica", 12)
            pdf.drawString(90, y, f"{key}. {val}")
            y -= 16

        y -= 8

    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    return buffer.read()
