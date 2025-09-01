import datetime
from dataclasses import dataclass
from threading import Event, Lock
from typing import Optional

from ._oauth_authority_client import OAuthAuthorityClient
from ._interfaces import Credentials, DatetimeProvider, SupportsRefresh
from ._token import OAuthToken


@dataclass
class TokenProviderOptions:
	token_expire_delta: datetime.timedelta = datetime.timedelta(seconds=20)


class TokenProvider:

	def __init__(
		self,
		authority: OAuthAuthorityClient,
		datetime_provider: Optional[DatetimeProvider] = None,
		options: Optional[TokenProviderOptions] = None,
	):
		self.authority = authority
		self.options = options or TokenProviderOptions()
		self.now = (
			lambda: (datetime_provider or datetime.datetime.now)()
			+ self.options.token_expire_delta
		)

		self.sync_token_providers: dict[Credentials, SyncTokenProvider] = {}

	def get_token(self, credentials: Credentials) -> OAuthToken:

		if not (provider := self.sync_token_providers.get(credentials)):
			provider = SyncTokenProvider(self.authority, self.now)
			self.sync_token_providers[credentials] = provider

		return provider.get_token(credentials)


class SyncTokenProvider:

	def __init__(
		self,
		authority: OAuthAuthorityClient,
		datetime_provider: DatetimeProvider,
	) -> None:
		self.authority = authority
		self.now = datetime_provider

		self.lock = Lock()
		self.event = Event()

		self.value: OAuthToken | None = None

	def get_token(self, credentials: Credentials) -> OAuthToken:

		while True:

			token = self.value

			if token:
				if not token.has_expired(self.now()):
					break

				self.event.clear()

			acquired = self.lock.acquire(blocking=False)

			if not acquired:
				_ = self.event.wait()
				continue

			try:
				if not self.event.is_set():
					token = self.fetch_token(credentials, token)
					self.value = token
					self.event.set()
			finally:
				self.lock.release()

		return token

	def fetch_token(
		self, credentials: Credentials, token: OAuthToken | None
	) -> OAuthToken:

		if token:

			if not token.has_expired(self.now()):
				return token

			if (
				self.authority.supports_grant("refresh_token")
				and isinstance(credentials, SupportsRefresh)
				and token.refresh_token
				and not token.refresh_token_has_expired(self.now())
			):
				return self.authority.get_token(
					credentials.refresh(token.refresh_token)
				)

		return self.authority.get_token(credentials)
