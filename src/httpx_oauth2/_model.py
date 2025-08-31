from typing import Optional

from ._interfaces import Credentials, GrantType, AuthMethods
from ._token import Scopes

DefaultAuthMethods: AuthMethods = ("client_secret_basic", "client_secret_post")


class ClientCredentials:
	def __init__(
		self,
		client_id: str,
		client_secret: Optional[str],
		scopes: Scopes = Scopes(),
		auth_methods: AuthMethods = DefaultAuthMethods,
	) -> None:
		self.client_id = client_id
		self.client_secret = client_secret
		self.scopes = scopes
		self.auth_methods = auth_methods

	def __str__(self) -> str:
		return f'ClientCredentials(client_id={self.client_id}, scopes={self.scopes})'

	@property
	def grant_type(self) -> GrantType:
		return "client_credentials"

	def to_request_body(self) -> dict[str, str]:
		return {}

	def key(self) -> str:
		return f"{self.client_id}:{self.scopes}"

	def exchange(self, subject_token: str) -> Credentials:
		return TokenExchangeCredentials(
			subject_token=subject_token,
			client_id=self.client_id,
			client_secret=self.client_secret,
			scopes=self.scopes,
			auth_methods=self.auth_methods,
		)

	def refresh(self, refresh_token: str) -> Credentials:
		return ClientCredentialsRefreshCredentials(
			refresh_token=refresh_token,
			client_id=self.client_id,
			client_secret=self.client_secret,
			scopes=self.scopes,
			auth_methods=self.auth_methods,
		)


class ResourceOwnerCredentials:
	def __init__(
		self,
		client_id: str,
		client_secret: Optional[str] = None,
		scopes: Scopes = Scopes(),
		auth_methods: AuthMethods = DefaultAuthMethods,
	) -> None:
		self.client_id = client_id
		self.client_secret = client_secret
		self.scopes = scopes
		self.auth_methods = auth_methods

	def __str__(self) -> str:
		return f'ResourceOwnerCredentials(client_id={self.client_id}, scopes={self.scopes})'

	def with_username_password(self, username: str, password: str):
		return ResourceOwnerCredentialsWithUser(
			username=username,
			password=password,
			client_id=self.client_id,
			client_secret=self.client_secret,
			scopes=self.scopes,
			auth_methods=self.auth_methods,
		)


class ResourceOwnerCredentialsWithUser:
	def __init__(
		self,
		client_id: str,
		client_secret: Optional[str],
		username: str,
		password: str,
		scopes: Scopes = Scopes(),
		auth_methods: AuthMethods = DefaultAuthMethods,
	) -> None:
		self.username = username
		self.password = password
		self.client_id = client_id
		self.client_secret = client_secret
		self.scopes = scopes
		self.auth_methods = auth_methods

	def __str__(self) -> str:
		return f'ResourceOwnerCredentialsWithUser(client_id={self.client_id}, scopes={self.scopes})'

	@property
	def grant_type(self) -> GrantType:
		return "password"

	def to_request_body(self) -> dict[str, str]:
		return {
			"username": self.username,
			"password": self.password,
		}

	def key(self) -> str:
		return f"{self.client_id}:{self.username}:{self.scopes}"

	def refresh(self, refresh_token: str) -> Credentials:
		return ResourceOwnerCredentialsRefreshCredentials(
			refresh_token=refresh_token,
			username=self.username,
			password=self.password,
			client_id=self.client_id,
			client_secret=self.client_secret,
			scopes=self.scopes,
			auth_methods=self.auth_methods,
		)


class TokenExchangeCredentials:
	def __init__(
		self,
		client_id: str,
		client_secret: Optional[str],
		subject_token: str,
		scopes: Scopes = Scopes(),
		auth_methods: AuthMethods = DefaultAuthMethods,
	) -> None:
		self.subject_token = subject_token
		self.client_id = client_id
		self.client_secret = client_secret
		self.scopes = scopes
		self.auth_methods = auth_methods

	def __str__(self) -> str:
		return f'TokenExchangeCredentials(client_id={self.client_id}, scopes={self.scopes})'

	@property
	def grant_type(self) -> GrantType:
		return "urn:ietf:params:oauth:grant-type:token-exchange"

	def to_request_body(self) -> dict[str, str]:
		return {
			"subject_token": self.subject_token,
			"subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
		}

	def key(self) -> str:
		return f"{self.client_id}:{self.subject_token}:{self.scopes}"

	def refresh(self, refresh_token: str) -> Credentials:
		return ClientCredentialsRefreshCredentials(
			refresh_token=refresh_token,
			client_id=self.client_id,
			client_secret=self.client_secret,
			scopes=self.scopes,
			auth_methods=self.auth_methods,
		)

	def client_credentials(self) -> Credentials:
		return ClientCredentials(
			client_id=self.client_id,
			client_secret=self.client_secret,
			scopes=self.scopes,
			auth_methods=self.auth_methods
		)


class ClientCredentialsRefreshCredentials:
	def __init__(
		self,
		client_id: str,
		client_secret: Optional[str]	,
		refresh_token: str,
		scopes: Scopes = Scopes(),
		auth_methods: AuthMethods = DefaultAuthMethods,
	) -> None:
		self.refresh_token = refresh_token
		self.client_id = client_id
		self.client_secret = client_secret
		self.scopes = scopes
		self.auth_methods = auth_methods

	def __str__(self) -> str:
		return f'ClientCredentialsRefreshCredentials(client_id={self.client_id}, scopes={self.scopes})'

	@property
	def grant_type(self) -> GrantType:
		return "refresh_token"

	def to_request_body(self) -> dict[str, str]:
		return {"refresh_token": self.refresh_token}

	def key(self) -> str:
		return f"{self.client_id}:{self.scopes}"


class ResourceOwnerCredentialsRefreshCredentials:
	def __init__(
		self,
		client_id: str,
		client_secret: Optional[str],
		username: str,
		password: str,
		refresh_token: str,
		scopes: Scopes = Scopes(),
		auth_methods: AuthMethods = DefaultAuthMethods,
	) -> None:
		self.refresh_token = refresh_token
		self.username = username
		self.password = password
		self.client_id = client_id
		self.client_secret = client_secret
		self.scopes = scopes
		self.auth_methods = auth_methods

	def __str__(self) -> str:
		return f'ResourceOwnerCredentialsRefreshCredentials(client_id={self.client_id}, scopes={self.scopes})'

	@property
	def grant_type(self) -> GrantType:
		return "refresh_token"

	def to_request_body(self) -> dict[str, str]:
		return {"refresh_token": self.refresh_token}

	def key(self) -> str:
		return f"{self.client_id}:{self.username}:{self.scopes}"
