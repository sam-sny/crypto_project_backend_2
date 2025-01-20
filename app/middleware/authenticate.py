""" Authentication middleware. """
from datetime import datetime, timezone
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends
from jose import jwt, JWTError
from sqlalchemy import orm
from app.database import SessionLocal, engine
from app.models.user import User, TokenBlacklist
#from api.models import payment_models
#from api.schemas import user_schemas


SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def is_authenticated(
    token: str = Depends(oauth2_scheme), db: orm.Session = Depends(get_db)
) -> User | None:
    """Check if user is authenticated.

    Args:
        token (str): JWT token
        db (Session, optional): Database session. Defaults to Depends(get_db).

    Returns:
        User | None: User object if authenticated, else None
    """
    # Check if token is empty
    if not token:
        print("Error: Token is empty")
        return None

    # Check if token is in the blacklist
    if _ := (
        db.query(TokenBlacklist)
        .filter(TokenBlacklist.token == token)
        .first()
    ):
        print("Error: Token is blacklisted")
        return None

    # Validate JWT token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            print("Error: User email is not in payload")
            return None
    except JWTError as jwe:
        print(f"Error: {jwe}")
        return None

    # Get user
    user = (
        db.query(User).filter(User.email == email).first()
    )

    # # If the user's subscription is expired and over 7 days, return None
    # if not user.is_subscribed:
    #     subscription = (
    #         db.query(payment_models.Subscription)
    #         .filter(payment_models.Subscription.user_id == user_id)
    #         .order_by(payment_models.Subscription.date_created.desc())
    #         .first()
    #     )
    #     if subscription.end_date:
    #         if datetime.now(timezone.utc) > subscription.end_date:
    #             if datetime.now(timezone.utc) - subscription.end_date > 7:
    #                 return None

    # if not user.is_subscribed:
    #     print("Error: User is not subscribed")
    #     return None

    return user


''' def is_superadmin(
    token: str = Depends(oauth2_scheme), db: orm.Session = Depends(get_db)
) -> user_model.User | None:
    """Check if user is authenticated and a superadmin.

    Args:
        token (str): JWT token
        db (Session, optional): Database session. Defaults to Depends(get_db).

    Returns:
        User | None: User object if authenticated, else None
    """
    # Check if token is empty
    if not token:
        print("Error: Token is empty")
        return None

    # Check if token is in the blacklist
    if _ := (
        db.query(user_model.TokenBlacklist)
        .filter(user_model.TokenBlacklist.token == token)
        .first()
    ):
        print("Error: Token is blacklisted")
        return None

    # Validate JWT token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            print("Error: User id is not in payload")
            return None
        expire = payload.get("exp")
        if expire is None:
            print("Error: Token has no expiry")
            return None
        if datetime.now(timezone.utc) > datetime.fromtimestamp(expire, timezone.utc):
            print("Error: Token has expired")
            return None
    except JWTError as jwe:
        print(f"Error: {jwe}")
        return None

    # Get user
    user = (
        db.query(user_model.User).filter(user_model.User.id == user_id).first()
    )

    # Check if user is a superadmin
    if not user.is_superadmin:
        print("Error: User is not a superadmin")
        return None

    return user '''