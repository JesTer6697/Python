def handler(request):
    import json
    import hashlib
    import hmac
    import random

    def byte_generator(server_seed, client_seed, nonce, cursor):
        seed = f"{client_seed}:{nonce}:{cursor}".encode()
        i = 0
        while True:
            h = hmac.new(server_seed.encode(), seed + i.to_bytes(4, 'big'), hashlib.sha256).digest()
            for b in h:
                yield b
            i += 1

    def generate_floats(server_seed, client_seed, nonce, cursor, count):
        rng = byte_generator(server_seed, client_seed, nonce, cursor)
        bytes_ = []
        while len(bytes_) < count * 4:
            bytes_.append(next(rng))
        chunks = [bytes_[i:i+4] for i in range(0, len(bytes_), 4)]
        return [sum(chunk[i] / 256**(i + 1) for i in range(4)) for chunk in chunks]

    try:
        if request.method != "POST":
            return {"statusCode": 405, "body": "Only POST allowed"}

        body = request.json
        client_seed = body["clientSeed"]
        server_seed = body["serverSeed"]
        unhashed_seed = body["unhashedSeed"]
        nonce = int(body["nonce"])
        mine_count = int(body["mineCount"])

        if not all([client_seed, server_seed, unhashed_seed]) or mine_count < 1 or mine_count > 24:
            raise ValueError("Missing or invalid input")

        floats = generate_floats(unhashed_seed, client_seed, nonce, 0, 25)
        paired = list(enumerate(floats))
        sorted_mines = sorted(paired, key=lambda x: x[1], reverse=True)
        mines = [idx for idx, _ in sorted_mines[:mine_count]]

        return {
            "statusCode": 200,
            "body": json.dumps({
                "success": True,
                "mines": mines
            })
        }
    except Exception as e:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "success": False,
                "error": str(e)
            })
        }
        