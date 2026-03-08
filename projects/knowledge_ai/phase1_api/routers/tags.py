"""routers/tags.py - タグ管理エンドポイント"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import TagDB, TagSchema

router = APIRouter(prefix="/tags", tags=["Tags"])


@router.get("", response_model=list[TagSchema])
async def list_tags(db: Session = Depends(get_db)):
    return db.query(TagDB).order_by(TagDB.name).all()


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    tag = db.query(TagDB).filter(TagDB.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail=f"Tag id={tag_id} が見つかりません")
    db.delete(tag)
    db.commit()
