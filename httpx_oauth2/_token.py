import datetime
from dataclasses import dataclass

Scopes = tuple[str, ...]


@dataclass(frozen=True)
class OAuthToken:

	token_type: str
	emitted_at: datetime.datetime

	access_token: str
	expires_in: datetime.timedelta

	refresh_token: str | None
	refresh_token_expires_in: datetime.timedelta

	scopes: Scopes

	def expiration(self, now: datetime.datetime) -> datetime.timedelta:
		"""Returns the nmber of second left before both the access_token and refres_token expires."""
		return (
			self.emitted_at + max(self.expires_in, self.refresh_token_expires_in) - now
		)

	def has_expired(self, now: datetime.datetime) -> bool:
		"""Returns True if the token has expired at the given time."""
		return self.emitted_at + self.expires_in <= now

	def refresh_token_has_expired(self, now: datetime.datetime) -> bool:
		"""Returns True if the refresh token has expired at the given time."""
		return self.emitted_at + self.refresh_token_expires_in <= now

	def to_bearer_string(self) -> str:
		"""Returns the string to put in the Authorization header."""
		return f"Bearer {self.access_token}"

	@classmethod
	def from_dict(cls, data: dict[str, str], *, emitted_at: datetime.datetime):
		return cls(
			token_type=data["token_type"],
			emitted_at=emitted_at,
			access_token=data["access_token"],
			expires_in=datetime.timedelta(seconds=int(data["expires_in"])),
			refresh_token=data.get("refresh_token"),
			refresh_token_expires_in=datetime.timedelta(
				seconds=int(data.get("refresh_expires_in", 0))
			),
			scopes=Scopes(data["scope"].split(" ")),
		)
