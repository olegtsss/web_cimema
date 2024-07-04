from fastapi import FastAPI

from schemas import UserEmail, UserProfile, UserSettings

app = FastAPI(title="Auth emulator")


@app.get(
    "/api/v1/users/{user_id}/profile",
    response_model=UserProfile,
)
def get_user_profile(user_id: str) -> UserProfile:
    return UserProfile()


@app.get(
    "/api/v1/users/{user_id}/email",
    response_model=UserEmail,
)
def get_user_email(user_id: str) -> UserEmail:
    return UserEmail()


@app.get(
    "/api/v1/users/{user_id}/settings",
    response_model=UserSettings,
)
def get_user_settings(user_id: str) -> UserSettings:
    return UserSettings()
