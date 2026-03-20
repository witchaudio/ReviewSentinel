from typing import List
from pydantic import BaseModel, Field, validator


class ReviewRequest(BaseModel):
    text: str
    rating: int = Field(..., ge=1, le=5)
    verified: bool
    helpful_votes: int = Field(default=0, ge=0)
    review_length: int = Field(default=None)

    @validator("review_length", always=True, pre=True)
    def default_review_length(cls, v, values):
        if v is None:
            return len(values.get("text", ""))
        return v


class ReviewResponse(BaseModel):
    score: float
    verdict: str
    reasons: List[str]
    color: str


class BatchReviewRequest(BaseModel):
    reviews: List[ReviewRequest] = Field(..., max_items=50)


class BatchReviewResponse(BaseModel):
    results: List[ReviewResponse]
