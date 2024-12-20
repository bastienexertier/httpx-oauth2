# HTTPX-OAuth2

My implementation of an `httpx.BaseTransport` that negotiates an access token and puts it in the request headers before sending it.

# Installation

You can't install it yet :(

# Usage

The library only needs to be setup. Once it is done, the authentication will happen behind the usage of `httpx.Client`, meaning you shouldn't need to change existing code.

## Imports

```python
import httpx
from httpx_oauth2 import (
	OAuthAuthorityClient,
	TokenProviderFactory,
	ClientAuthenticationTransport,
	ClientCredentials,
	ResourceOwnerCredentials
)
```

## Client Credentials

```python

api_client = httpx.Client(base_url='http://example')

# ============== ADD THIS ==============

token_providers = TokenProviderFactory(
	OAuthAuthorityClient(httpx.Client(base_url='http://localhost:8080/realms/master'))
)

credentials = ClientCredentials(CLIENT_ID, CLIENT_SECRET, ('scope-1', 'scope-2'))

api_client._transport = ClientAuthenticationTransport(
	api_client._transport,
	token_providers.client_credentials(credentials)
)

# ===== JUST THIS. NOW USE A USUAL =====

api_client.get('/users')

```

## Resource Owner

```python

api_client = httpx.Client(base_url='http://example')

# ============== ADD THIS ==============

token_providers = TokenProviderFactory(
	OAuthAuthorityClient(httpx.Client(base_url='http://localhost:8080/realms/master'))
)

credentials = ResourceOwnerCredentials(USERNAME, PASSWORD, CLIENT_ID, ('scope-1', 'scope-2')) # <<<

api_client._transport = ClientAuthenticationTransport(
	api_client._transport,
	token_providers.resource_owner(credentials) # <<<
)

# ===== JUST THIS. NOW USE A USUAL =====

api_client.get('/users')

```

## Token Exchange

```python

api_client = httpx.Client(base_url='http://example')

# ============== ADD THIS ==============

token_providers = TokenProviderFactory(
	OAuthAuthorityClient(httpx.Client(base_url='http://localhost:8080/realms/master'))
)

credentials = ClientCredentials(CLIENT_ID, CLIENT_SECRET, ('scope-1', 'scope-2'))

api_client._transport = TokenExchangeAuthenticationTransport( # <<<
	api_client._transport,
	token_providers.token_exchange(credentials) # <<<
)

# ===== JUST THIS. NOW USE A USUAL =====

# * Put the token to be exchanged in the authorization headers

api_client.get('/users', headers={'Authorization': 'token_to_be_exchanged'})

```

## Cache and Automatic retry

Access token are cached. Exchanged tokens too.  

If the AuthenticationTransport see that the response is 401 (meaning the token wasn't valid anymore), it will:
- Try to refresh the token with the refresh_token if supported.
- Request a new token.
- Re-send the request.


## But '\_' means its protected?

Yes. But I haven't found an easier way to let `httpx` build the base transport but still be able to wrap it with custom behavior.
