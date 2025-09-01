import datetime
import base64
from typing import Callable, Optional

import httpx

from ._interfaces import Credentials, SubjectTokenProvider, SupportsExchange, OAuthAuthorityError, DatetimeProvider
from ._oauth_authority_client import OAuthAuthorityClient
from ._model import ResourceOwnerCredentials
from ._token import OAuthToken
from ._token_provider import TokenProvider


class AuthenticatingTransport(httpx.BaseTransport):
	def __init__(
		self,
		transport: httpx.BaseTransport,
		credentials_builder: Callable[[httpx.Request], Optional[Credentials]],
		token_provider: TokenProvider,
	):
		self.transport = transport
		self.credentials_builder = credentials_builder
		self.token_provider = token_provider

	def handle_request(self, request: httpx.Request) -> httpx.Response:

		credentials = self.credentials_builder(request)

		if not credentials:
			raise OAuthAuthorityError('Failed to build credentials')

		response: Optional[httpx.Response] = None

		for _ in range(3):

			token = self.token_provider.get_token(credentials)

			request = set_auth_header(request, token)

			response = self.transport.handle_request(request)

			if response.status_code != 401:
				return response

		if response is not None:
			return response

		raise OAuthAuthorityError('Failed to get token')


class AuthenticatingTransportFactory:
	def __init__(
		self,
		authority: OAuthAuthorityClient,
		datetime_provider: Optional[DatetimeProvider] = None,
	):
		self.token_provider = TokenProvider(authority, datetime_provider or datetime.datetime.now)

	def auhtenticating_transport(
		self, transport: httpx.BaseTransport, credentials: Credentials
	) -> httpx.BaseTransport:
		"""Authenticate calls with client_credential or password grant"""
		return AuthenticatingTransport(
			transport,
			lambda req: build_credentials(req, credentials),
			self.token_provider,
		)

	def resource_owner_transport(
		self, transport: httpx.BaseTransport, credentials: ResourceOwnerCredentials
	) -> httpx.BaseTransport:
		"""Authenticate calls with password grant, where the username/password is taken from the Authorization header"""
		return AuthenticatingTransport(
			transport,
			lambda req: add_username_password(req, credentials),
			self.token_provider,
		)

	def token_exchange_transport(
		self,
		transport: httpx.BaseTransport,
		credentials: SupportsExchange,
		subject_token_provider: SubjectTokenProvider,
		optional_exchange: bool=False,
	) -> httpx.BaseTransport:
		"""
		Authenticate calls with token-exhange grant.
		The subject token is given by the subject_token_provider.
		If optional_exchange is True and no subject_token is return, will try requesting the resource without exchange.
		(ie with client credentials or password)
		"""
		return AuthenticatingTransport(
			transport,
			lambda req: build_exchange_credentials(
				req,
				credentials,
				subject_token_provider,
				optional_exchange
			),
			self.token_provider,
		)

def set_auth_header(request: httpx.Request, token: OAuthToken) -> httpx.Request:
	request.headers["Authorization"] = token.to_bearer_string()
	return request


def build_credentials(
	request: httpx.Request, credentials: Credentials
) -> Optional[Credentials]:
	return credentials if "Authorization" not in request.headers else None


def add_username_password(
	request: httpx.Request, credentials: ResourceOwnerCredentials
) -> Optional[Credentials]:

	auth_header = request.headers.get("Authorization")
	if not auth_header:
		return None

	username, password = (
		base64.b64decode(auth_header.removeprefix("Basic ")).decode("utf-8").split(":")
	)

	return credentials.with_username_password(username, password)


def build_exchange_credentials(
	request: httpx.Request,
	credentials: SupportsExchange,
	subject_token_provider: SubjectTokenProvider,
	optional_exchange: bool
) -> Optional[Credentials]:

	subject_token = subject_token_provider()

	if subject_token:
		return credentials.exchange(subject_token)

	if optional_exchange:
		return credentials

	raise OAuthAuthorityError('Failed to acquire subject token')
