import datetime
from dataclasses import dataclass
from typing import Iterator, Optional

from cachelib.simple import SimpleCache

from ._oauth_authority_client import OAuthAuthorityClient
from ._interfaces import DatetimeProvider, SupportsRefresh
from ._model import Credentials
from ._token import OAuthToken


@dataclass
class TokenProviderOptions:
	token_expire_delta: datetime.timedelta = datetime.timedelta(seconds=20)


class TokenProvider:

	token_cache = SimpleCache(threshold=100)

	def __init__(
		self,
		authority: OAuthAuthorityClient,
		datetime_provider: Optional[DatetimeProvider] = None,
	):
		self.authority = authority
		self.options = TokenProviderOptions()
		self.now = (
			lambda: (datetime_provider or datetime.datetime.now)()
			+ self.options.token_expire_delta
		)

	def get_token(self, credentials: Credentials) -> Iterator[OAuthToken]:

		key = credentials.key()

		token: Optional[OAuthToken] = self.token_cache.get(key)

		if token:
			if not token.has_expired(self.now()):
				yield token

			if (
				self.authority.supports_grant("refresh_token")
				and isinstance(credentials, SupportsRefresh)
				and token.refresh_token
				and not token.refresh_token_has_expired(self.now())
			):
				token = self.authority.get_token(
					credentials.refresh(token.refresh_token)
				)

				self.token_cache.set(
					key, token, timeout=token.expiration(self.now()).seconds
				)
				yield token

		token = self.authority.get_token(credentials)

		self.token_cache.set(key, token, timeout=token.expiration(self.now()).seconds)
		yield token
		self.token_cache.delete(key)
