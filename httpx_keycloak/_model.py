
import datetime
from dataclasses import dataclass


Scopes = tuple[str, ...]


@dataclass(frozen=True)
class KeycloakToken:

	token_type: str
	access_token: str
	emitted_at: datetime.datetime
	expires_in: datetime.timedelta
	scopes: Scopes

	def has_expired(self, now: datetime.datetime) -> bool:
		""" Returns True if the token has expired at the given time. """
		return self.emitted_at + self.expires_in <= now

	def to_bearer_string(self) -> str:
		""" Returns the string to put in the Authorization header. """
		return f'Bearer {self.access_token}'

	@classmethod
	def from_dict(cls, data: dict[str, str], *, emitted_at: datetime.datetime):
		return cls(
			token_type=data['token_type'],
			access_token=data['access_token'],
			emitted_at=emitted_at,
			expires_in=datetime.timedelta(seconds=int(data['expires_in'])),
			scopes=Scopes(data['scope'].split(' '))
		)


@dataclass
class ClientCredentials:

	client_id: str
	client_secret: str
	scopes: Scopes = Scopes()

	def with_scopes(self, scopes: Scopes):
		""" Returns a copy of the credentials with the given scopes """
		return self.__class__(self.client_id, self.client_secret, scopes)

	def request_body(self) -> dict[str, str]:
		data = {
			"client_id": self.client_id,
			"client_secret": self.client_secret,
			"grant_type": "client_credentials"
		}

		if self.scopes:
			data["scope"] = str.join(' ', self.scopes)

		return data

@dataclass
class ResourceOwnerCredentials:

	username: str
	password: str

	client_id: str
	scopes: Scopes = Scopes()

	def with_scopes(self, scopes: Scopes):
		""" Returns a copy of the credentials with the given scopes """
		return self.__class__(self.username, self.password, self.client_id, scopes)

	def request_body(self) -> dict[str, str]:
		data = {
				"username": self.username,
				"password": self.password,
				"client_id": self.client_id,
				"grant_type": "password",
			}

		if self.scopes:
			data["scope"] = str.join(' ', self.scopes)

		return data
