from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.models.user import User
from app.schemas.schema import UserCreate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user: UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        is_google_user=False,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
        profile_image=user.profile_image,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
