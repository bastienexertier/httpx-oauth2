
import datetime
from dataclasses import dataclass
from typing import Iterator, Optional

from cachelib.simple import SimpleCache

from ._oauth_authority_client import OAuthAuthorityClient
from ._interfaces import DatetimeProvider, SupportsRefresh
from ._model import Credentials
from ._token import KeycloakToken

@dataclass
class TokenProviderOptions:
	token_expire_delta: datetime.timedelta = datetime.timedelta(seconds=20)

class TokenProvider:

	token_cache = SimpleCache(threshold=100)

	def __init__(self, keycloak_client: OAuthAuthorityClient, datetime_provider: Optional[DatetimeProvider]=None):
		self.keycloak = keycloak_client
		self.options = TokenProviderOptions()
		self.now = lambda: (datetime_provider or datetime.datetime.now)() + self.options.token_expire_delta

	def get_token(self, credentials: Credentials) -> Iterator[KeycloakToken]:

		key = credentials.key()

		token: Optional[KeycloakToken] = self.token_cache.get(key)

		if token:
			if not token.has_expired(self.now()):
				yield token

			if (
				self.keycloak.supports_grant('refresh_token')
				and isinstance(credentials, SupportsRefresh)
				and token.refresh_token
				and not token.refresh_token_has_expired(self.now())
			):
				token = self.keycloak.get_token(credentials.refresh(token.refresh_token))

				self.token_cache.set(key, token, timeout=token.expiration(self.now()).seconds)
				yield token

		token = self.keycloak.get_token(credentials)

		self.token_cache.set(key, token, timeout=token.expiration(self.now()).seconds)
		yield token
		self.token_cache.delete(key)
