import datetime
from typing import Optional, Literal, Callable, Protocol, runtime_checkable

from ._token import Scopes

GrantType = Literal[
	"authorization_code",
	"implicit",
	"refresh_token",
	"password",
	"client_credentials",
	"urn:openid:params:grant-type:ciba",
	"urn:ietf:params:oauth:grant-type:token-exchange",
	"urn:ietf:params:oauth:grant-type:device_code",
]

AuthMethod = Literal[
	"private_key_jwt",
	"client_secret_basic",
	"client_secret_post",
	"tls_client_auth",
	"client_secret_jwt",
]

AuthMethods = tuple[AuthMethod, ...]


class OAuthAuthorityError(Exception): ...


DatetimeProvider = Callable[[], datetime.datetime]
SubjectTokenProvider = Callable[[], Optional[str]]


class Credentials(Protocol):

	auth_methods: AuthMethods

	@property
	def grant_type(self) -> GrantType: ...

	@property
	def client_id(self) -> str: ...

	@property
	def client_secret(self) -> Optional[str]: ...

	@property
	def scopes(self) -> Scopes: ...

	def to_request_body(self) -> dict[str, str]: ...


class SupportsExchange(Credentials, Protocol):
	def exchange(self, subject_token: str) -> Credentials: ...


@runtime_checkable
class SupportsRefresh(Credentials, Protocol):
	def refresh(self, refresh_token: str) -> Credentials: ...
