
import datetime
from typing import Optional, Literal, Callable, Protocol, Iterator, runtime_checkable


from ._token import KeycloakToken, Scopes


GrantType = Literal[
	"authorization_code",
	"implicit",
	"refresh_token",
	"password",
	"client_credentials",
	"urn:openid:params:grant-type:ciba",
	"urn:ietf:params:oauth:grant-type:token-exchange",
	"urn:ietf:params:oauth:grant-type:device_code"
]


class KeycloakError(Exception):
	...


DatetimeProvider = Callable[[], datetime.datetime]



class TokenRequest(Protocol):

	@property
	def grant_type(self) -> GrantType:
		...

	@property
	def client_id(self) -> str:
		...

	@property
	def client_secret(self) -> Optional[str]:
		...

	@property
	def scopes(self) -> Scopes:
		...

	def to_request_body(self) -> dict[str, str]:
		...


@runtime_checkable
class SupportsExhange(TokenRequest, Protocol):

	def exchange(self, subject_token: str) -> TokenRequest:
		...

@runtime_checkable
class SupportsRefresh(TokenRequest, Protocol):

	def refresh(self, refresh_token: str) -> TokenRequest:
		...


class TokenProvider(Protocol):

	def get_token(self) -> Iterator[KeycloakToken]:
		...


class TokenExchanger(Protocol):

	def exchange_token(self, subject_token: str) -> Iterator[KeycloakToken]:
		...
