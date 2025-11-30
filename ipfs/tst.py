from stellar_sdk import Keypair

issuer = Keypair.random()
print("PUBLIC:", issuer.public_key)
print("SECRET:", issuer.secret)

