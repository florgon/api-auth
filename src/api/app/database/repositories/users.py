"""
    Users repository.
"""

from app.database.models.user import User
from app.database.repositories.base import BaseRepository
from app.services.passwords import HashingError, get_hashed_password


class UsersRepository(BaseRepository):
    """
    Users database CRUD repository.
    """

    def get_user_by_email(self, email: str) -> User | None:
        """Returns user by email."""
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_username(self, username: str) -> User | None:
        """Returns user by username."""
        return self.db.query(User).filter(User.username == username).first()

    def get_user_by_login(self, login: str) -> User | None:
        """Returns user by login."""
        user = self.get_user_by_username(username=login)
        if not user:
            return self.get_user_by_email(email=login)
        return user

    def get_user_by_id(self, user_id: int) -> User | None:
        """Returns user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def create(self, username: str, email: str, password: str) -> User | None:
        """Creates user with given credentials."""
        # Create new user.
        try:
            hashed_password = get_hashed_password(password, hash_method=None)
        except HashingError:
            return None
        user = User(
            username=username,
            email=email,
            password=hashed_password,
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
