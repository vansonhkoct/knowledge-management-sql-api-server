"""Authenticate sockets using host-only cookies from customer frontend profiles."""

async def authenticate_party_socket(websocket, party_id, authenticate=None):
    if authenticate is None:
        from src.controllers.functions.user.userauth_session import obtain_user_by_user_access_token
        authenticate = obtain_user_by_user_access_token
    cookies = websocket.cookies
    candidates = [cookies.get(f"{party_id}_access_token"), cookies.get("access_token")]
    # Administration profiles have a customer-key prefix rather than a fixed party ID.
    candidates.extend(value for name, value in cookies.items() if name.endswith("_access_token"))
    candidates.append(websocket.query_params.get("access_token"))  # Legacy clients.
    seen = set()
    for token in candidates:
        if not token or token in seen:
            continue
        seen.add(token)
        try:
            user = await authenticate(access_token=token)
        except Exception:
            continue
        if user is not None and str(user.party_id) == str(party_id):
            return user
    return None
