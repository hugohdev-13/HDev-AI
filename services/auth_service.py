from werkzeug.security import check_password_hash

from repositories.auth_repository import AuthRepository


class AuthService:

    @staticmethod
    def authenticate(email, password):

        user = AuthRepository.get_by_email(email)

        if user is None:
            return None

        if not check_password_hash(
            user.password_hash,
            password
        ):
            return None

        return user