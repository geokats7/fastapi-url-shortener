from statistics import mode
from urllib import request
import validators
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from shortener_app import crud, models, schemas
from shortener_app.database import SessionLocal, engine


app = FastAPI()
models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def raise_bad_request(message: str) -> None:
    raise HTTPException(status_code=400, detail=message)

def raise_not_found(request) -> None:
    message = f"URL '{request.url}' doesn't exist"
    raise HTTPException(status_code=404, detail=message)


@app.get("/")
def read_root():
    return "Hello, World!"

@app.post("/url", response_model=schemas.URLInfo)
def create_url(url: schemas.URLBase, db: Session = Depends(get_db)):
    if not validators.url(url.target_url):
        raise_bad_request("Invalid URL")

    db_url = crud.create_db_url(db=db, url=url)
    db_url.url = db_url.key
    db_url.admin_url = db_url.secret_key

    return db_url


@app.get("/{url_key}")
def forward_to_target_url(
    url_key: str,
    request: Request,
    db: Session = Depends(get_db)
):
    if db_url := crud.get_db_url_by_key(db=db, key=url_key):
        return RedirectResponse(db_url.target_url)
    
    raise_not_found(request)