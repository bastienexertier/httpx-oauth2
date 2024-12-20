import datetime
import base64
from typing import Callable, Optional

import httpx

from ._interfaces import Credentials, SupportsExhange, KeycloakError, DatetimeProvider
from ._oauth_authority_client import OAuthAuthorityClient
from ._model import (
	ClientCredentials,
	ResourceOwnerCredentials,
	ResourceOwnerCredentialsWithUser,
)
from ._token import KeycloakToken
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

		response = None
		if credentials:

			for token in self.token_provider.get_token(credentials):

				set_auth_header(request, token)

				response = self.transport.handle_request(request)

				if response.status_code != 401:
					return response

		return response or self.transport.handle_request(request)


class AuthenticatingTransportFactory:
	def __init__(
		self,
		keycloak_client: OAuthAuthorityClient,
		datetime_provider: Optional[DatetimeProvider] = None,
	):
		self.keycloak = keycloak_client
		self.now = datetime_provider or datetime.datetime.now

	def client_credentials_transport(
		self, transport: httpx.BaseTransport, credentials: ClientCredentials
	) -> httpx.BaseTransport:
		"""Authenticate calls with client_credential grant"""
		return AuthenticatingTransport(
			transport,
			lambda req: build_credentials(req, credentials),
			TokenProvider(self.keycloak, self.now),
		)

	def technical_account_transport(
		self,
		transport: httpx.BaseTransport,
		credentials: ResourceOwnerCredentialsWithUser,
	) -> httpx.BaseTransport:
		"""Authenticate calls with password grant, where the username/password is unique and set in credentials"""
		return AuthenticatingTransport(
			transport,
			lambda req: build_credentials(req, credentials),
			TokenProvider(self.keycloak, self.now),
		)

	def resource_owner_transport(
		self, transport: httpx.BaseTransport, credentials: ResourceOwnerCredentials
	) -> httpx.BaseTransport:
		"""Authenticate calls with password grant, where the username/password is taken from the Authorization header"""
		return AuthenticatingTransport(
			transport,
			lambda req: add_username_password(req, credentials),
			TokenProvider(self.keycloak, self.now),
		)

	def token_exchange_transport(
		self, transport: httpx.BaseTransport, credentials: SupportsExhange
	) -> httpx.BaseTransport:
		"""Authenticate calls with token-exhange grant, where the subject token is taken from the Authorization header"""
		return AuthenticatingTransport(
			transport,
			lambda req: build_exchange_credentials(req, credentials),
			TokenProvider(self.keycloak, self.now),
		)


def set_auth_header(request: httpx.Request, token: KeycloakToken):
	request.headers["Authorization"] = token.to_bearer_string()


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
	request: httpx.Request, credentials: SupportsExhange
) -> Optional[Credentials]:
	auth_header: str = request.headers.get("Authorization")

	if not auth_header:
		raise KeycloakError("Token to be exchanged not found in Authorization header")

	return credentials.exchange(auth_header.removeprefix("Bearer "))
