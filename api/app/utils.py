from django.contrib.auth import authenticate
import json
import jwt
import requests
import os
from dotenv import load_dotenv
load_dotenv()

# Maps the sub field from the access_token to the username
def jwt_get_username_from_payload_handler(payload):
    username = payload.get('sub').replace('|', '.')
    authenticate(remote_user=username)
    return username

# Fetches the JWKS from Auth0 to verify and decode the incoming Access Token
def jwt_decode_token(token):
    header = jwt.get_unverified_header(token)
    jwks = requests.get('https://{}/.well-known/jwks.json'.format(os.getenv('AUTH_DOMAIN'))).json()
    public_key = None
    for jwk in jwks['keys']:
        if jwk['kid'] == header['kid']:
            public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
            break
    if public_key is None:
        print("we don't go here")
        raise Exception('Public key not found')

    issuer = 'https://{}/'.format(os.getenv('AUTH_DOMAIN'))
    return jwt.decode(token, public_key, audience=os.getenv('AUTH_AUDIENCE'), issuer=issuer, algorithms=['RS256'])