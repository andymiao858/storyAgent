from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.response import success_response, error_response
from app.core.security import hash_password, verify_password, create_access_token
from app.db.session import get_db
from app.models.user import User
from app.models.parent_settings import ParentSettings
from app.schemas.auth import RegisterRequest, LoginRequest

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="该邮箱已注册")

    user = User(
        email=req.email,
        password_hash=hash_password(req.password),
        role="parent",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Auto-create default parent settings
    settings_obj = ParentSettings(parent_id=user.id)
    db.add(settings_obj)
    db.commit()

    token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return success_response(
        data={"access_token": token, "token_type": "bearer", "user": {"id": user.id, "email": user.email, "role": user.role}}
    )


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="邮箱或密码错误")

    token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return success_response(
        data={"access_token": token, "token_type": "bearer", "user": {"id": user.id, "email": user.email, "role": user.role}}
    )


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return success_response(
        data={"id": current_user.id, "email": current_user.email, "role": current_user.role}
    )
