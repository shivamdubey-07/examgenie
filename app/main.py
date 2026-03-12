from fastapi import FastAPI


app = FastAPI(title="ExamGenie API")


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "ExamGenie API is running"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
