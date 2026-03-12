from app.worker.celery_app import celery_app


@celery_app.task
def generate_exam_task(exam_id: str) -> dict:
    # TODO: implement AI generation + validation + persistence
    return {"exam_id": exam_id, "status": "queued"}


@celery_app.task
def generate_pdf_task(exam_id: str) -> dict:
    # TODO: implement PDF generation + upload to storage
    return {"exam_id": exam_id, "status": "queued"}
