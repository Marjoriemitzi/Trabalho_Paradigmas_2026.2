from app.users.application.dtos.get_current_user import UserProfile


class GetCurrentUserPresenterSpy:
    def __init__(self) -> None:
        self.user: UserProfile | None = None
        self.user_not_found = False

    def present_user(self, user: UserProfile) -> None:
        self.user = user

    def present_user_not_found(self) -> None:
        self.user_not_found = True
