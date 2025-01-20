from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.security import OAuth2PasswordBearer
from fastapi_sso.sso.google import GoogleSSO
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from jose import JWTError, jwt
from google.auth.transport.requests import Request
from google.oauth2 import id_token
import requests
from app import crud
from app.models import user
from app.middleware.authenticate import is_authenticated
from app.schemas import schema
from app.database import SessionLocal, engine
from dotenv import load_dotenv
import os
from smtplib import SMTP_SSL
from email.mime.text import MIMEText
from datetime import datetime, timedelta

load_dotenv()

# Access the variables
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
redirect_uri = os.getenv("REDIRECT_URI")
scope = "openid email profile"
google_oauth_url = "https://accounts.google.com/o/oauth2/v2/auth"

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FRONTEND_URL = os.getenv("FRONTEND_URL")

#user.Base.metadata.drop_all(bind=engine)

user.Base.metadata.create_all(bind=engine)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

app = FastAPI()

origins = [
    "http://localhost:3000",  # Allow your frontend development server
    "https://tradeinvortex.org/*" # Add more origins if needed
]

# Add CORSMiddleware to your app
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows all origins listed above
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)


google_sso = GoogleSSO(client_id, client_secret, redirect_uri)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def send_email(subject: str, recipient: str, body: str):
    msg = MIMEText(body, "html")
    msg["Subject"] = subject
    msg["From"] = SMTP_USERNAME
    msg["To"] = recipient

    with SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=60) as server:
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SMTP_USERNAME, recipient, msg.as_string())

def get_current_user(token: str, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=400, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    # Activate user account
    db_user = crud.get_user_by_email(db, email=email)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    # Create a dictionary that matches the Pydantic schema
    

    # Validate and return the user profile
    return schema.UserProfile.model_validate(db_user)
    
# Sign Up
@app.post("/auth/signup")
def signup(user: schema.UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create the user
    created_user = crud.create_user(db=db, user=user)

    # Generate a verification token
    expiration = datetime.now() + timedelta(minutes=3)
    verification_token = jwt.encode(
        {
           "sub": user.email,  # Subject of the token
           "id": created_user.id,  # Add user id to the token
           "exp": expiration  # Expiration time
        }, SECRET_KEY, algorithm=ALGORITHM
    )

    # Verification link
    #verification_link = f"{FRONTEND_URL}/profile/overview?token={verification_token}"

    # Email content
    #email_subject = "Verify Your Email"
    #email_body = f"""
    #<p>Thank you for signing up!</p>
    #<p>Please click the link below to verify your email. This link will expire in 3 minutes:</p>
    #<a href="{verification_link}">Verify Email</a>
   # """

    # Send email in the background
    #background_tasks.add_task(send_email, email_subject, user.email, email_body)

    return {"message": "User created successfully. Please check your email to verify your account."}

# Email verification endpoint
@app.get("/auth/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=400, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    # Activate user account
    db_user = crud.get_user_by_email(db, email=email)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    #db_user.is_verified = True
    db.commit()
    return RedirectResponse(url=f"{FRONTEND_URL}/profile/overview")


# Login
@app.post("/auth/login")
def login(form_data: schema.UserLoginRequest, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, email=form_data.email)
    if not user or not crud.pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = jwt.encode({"sub": user.email}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer", "user": user}


# Google Sign-In Redirect
@app.get("/login/google")
async def google_login():
    """Generate login url and redirect"""
    auth_url = (
        f"{google_oauth_url}?response_type=code&client_id={client_id}"
        f"&redirect_uri={redirect_uri}&scope={scope}"
    )

    return RedirectResponse(url=auth_url)

# Process login request from google and return user data with access token

@app.get("/api/profile", response_model=schema.UserProfile)
def get_profile(current_user: schema.UserToken = Depends(is_authenticated)):
    """
    Endpoint to fetch the profile details of the logged-in user.
    """
    return current_user