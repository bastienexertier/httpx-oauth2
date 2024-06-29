
import datetime
from typing import TypedDict, Optional

import httpx

from ._interfaces import DatetimeProvider, KeycloakError, TokenRequest
from ._token import KeycloakToken
from ._model import GrantType


class OpenIDConfiguration(TypedDict):
	issuer: str
	authorization_endpoint: str
	token_endpoint: str
	introspection_endpoint: str
	userinfo_endpoint: str
	end_session_endpoint: str
	token_endpoint_auth_methods_supported: list[str]
	grant_types_supported: list[str]


class KeycloakClient:

	def __init__(self, http: httpx.Client, datetime_provider: Optional[DatetimeProvider]=None):
		self.http = http
		self.now = datetime_provider or datetime.datetime.now
		self.__openid_config: Optional[OpenIDConfiguration] = None


	def load_openid_config(self) -> OpenIDConfiguration:
		response = self.http.get('/.well-known/openid-configuration/')

		if response.status_code == 404:
			raise KeycloakError(f'OpenID configuration not found at {response.url}')

		return response.json()

	@property
	def openid_config(self) -> OpenIDConfiguration:
		if not self.__openid_config:
			self.__openid_config = self.load_openid_config()
		return self.__openid_config

	def supports_grant(self, grant: GrantType) -> bool:
		return grant in self.openid_config['grant_types_supported']

	def get_token(self, token_request: TokenRequest) -> KeycloakToken:
		"""
		Requests a new token from a TokenRequest.
		A TokenRequest is an object that can provide a Authentication header and request body.
		"""

		openid_config = self.openid_config

		auth_methods_supported = openid_config['token_endpoint_auth_methods_supported']

		auth = None
		request_body: dict[str, str]
		request_body = {'grant_type': token_request.grant_type}
		request_body |= token_request.to_request_body()

		auth_method = None
		for auth_method in token_request.auth_methods:

			if auth_method not in auth_methods_supported:
				continue

		if auth_method == 'client_secret_basic':
			auth = httpx.BasicAuth(token_request.client_id, token_request.client_secret or '')
		elif auth_method == 'client_secret_post':
			request_body['client_id'] = token_request.client_id
			if token_request.client_secret:
				request_body['client_secret'] = token_request.client_secret
		elif auth_method == 'client_secret_jwt':
			import time
			import uuid
			import jwt
			epoch_time = int(time.time())
			client_assertion = jwt.encode({
				"iss": token_request.client_id,
				"sub": token_request.client_id,
				"aud": self.openid_config['token_endpoint'],
				"jti": str(uuid.uuid4()),
				"exp": epoch_time+1000
			}, token_request.client_secret, algorithm="HS256")

			request_body['client_assertion_type'] = 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer'
			request_body['client_assertion'] = client_assertion


		else:
			raise KeycloakError('No token auth method supported')

		if token_request.scopes:
			request_body["scope"] = str.join(" ", token_request.scopes)

		response = self.http.post(
			openid_config['token_endpoint'],
			data=request_body,
			auth=auth or httpx.USE_CLIENT_DEFAULT
		)

		data = response.json()

		if response.is_error:
			raise KeycloakError(f"[{response.status_code}] {data['error']} - {data['error_description']}")

		return KeycloakToken.from_dict(data, emitted_at=self.now() - response.elapsed)
