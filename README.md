# HTTPX-OAuth2

My implementation of an `httpx.BaseTransport` that negotiates an access token and puts it in the request headers before sending it.

# Installation

`pip install httpx-oauth2`

# Usage

The library only needs to be setup. Once it is done, the authentication will happen behind the usage of `httpx.Client`, meaning **you shouldn't need to change existing httpx code**.

## Imports

```python
import httpx
from httpx_oauth2 import (
	OAuthAuthorityClient,
	ClientCredentials,
	ResourceOwnerCredentials,
	AuthenticatingTransportFactory
)
```

## Client Credentials

```python

api_client = httpx.Client(base_url='http://example')

# ============== ADD THIS ==============

oauth_authority = OAuthAuthorityClient(
	httpx.Client(base_url='http://localhost:8080/realms/master'),
)

transports = AuthenticatingTransportFactory(oauth_authority)

credentials = ClientCredentials('client-1', 'my-secret', ('scope-1',))

api_client._transport = transports.authenticating_transport(api_client._transport, credentials)

# ===== JUST THIS. NOW USE A USUAL =====

api_client.get('/users')

```

## Resource Owner (Client Credentials with a technical account)

```python

api_client = httpx.Client(base_url='http://example')

# ============== ADD THIS ==============

oauth_authority = OAuthAuthorityClient(
	httpx.Client(base_url='http://localhost:8080/realms/master'),
)

transports = AuthenticatingTransportFactory(oauth_authority)

credentials = ResourceOwnerCredentials('client-3', 'my-secret').with_username_password('user', 'pwd')

api_client._transport = transports.authenticating_transport(api_client._transport, credentials)

# ===== JUST THIS. NOW USE A USUAL =====

api_client.get('/users')

```

## Token Exchange

```python

api_client = httpx.Client(base_url='http://example')

# ============== ADD THIS ==============

oauth_authority = OAuthAuthorityClient(
	httpx.Client(base_url='http://localhost:8080/realms/master'),
)

transports = AuthenticatingTransportFactory(oauth_authority)

credentials = ClientCredentials('client-1', 'my-secret', ('scope-1',))

api_client._transport = transports.token_exchange_transport(
	api_client._transport,
	credentials,
	lambda: flask.request.headers['Authorization'].removeprefix('Bearer ') # A callable that returns the token to be exchanged
)

# ===== JUST THIS. NOW USE A USUAL =====

api_client.get('/users')

```

## Getting an access token

```python

oauth_authority = OAuthAuthorityClient(
	httpx.Client(base_url='http://localhost:8080/realms/master'),
)

credentials = ClientCredentials('client-1', 'my-secret', ('scope-1',))

token = oauth_authority.get_token(credentials)
```

## Cache and Automatic retry

Access token are cached. Exchanged tokens too.  

If the `AuthenticatingTransport` see that the response is 401 (meaning the token wasn't valid anymore), it will:
- Try to refresh the token with the refresh_token if supported.
- Request a new token.
- Re-send the request.

## Multithreading

The Token negotiation is behind a thread synchronization mechanism, meaning if multiple threads need a token at the same time, only one token will be negotiated with the authority and shared across all threads.

## But '\_' means its protected?

Yes. But I haven't found an easier way to let `httpx` build the base transport but still be able to wrap it with custom behavior.
