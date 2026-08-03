from models import User


class AuthRepository:

    @staticmethod
    def get_by_email(email):
        return User.query.filter_by(email=email).first()