from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from detector import explain_review
from models import ReviewRequest, ReviewResponse, BatchReviewRequest, BatchReviewResponse

app = FastAPI(title="ReviewSentinel API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/score", response_model=ReviewResponse)
def score(req: ReviewRequest):
    result = explain_review(req.dict())
    return ReviewResponse(**result)


@app.post("/score/batch", response_model=BatchReviewResponse)
def score_batch(req: BatchReviewRequest):
    results = [ReviewResponse(**explain_review(r.dict())) for r in req.reviews]
    return BatchReviewResponse(results=results)
