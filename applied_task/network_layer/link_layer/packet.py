class Packet:
    id: int
    data: bytes

    def __init__(self, id_: int, data: bytes):
        self.id = id_
        self.data = data
