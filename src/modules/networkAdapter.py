import enum
class NetworkTypes(enum.Enum):
    bridged = 1
    nat = 2
    hostOnly = 3

class NetworkAdapter:
    def __init__(self, enabled: bool, type: NetworkTypes) -> None:
        self.enabled = enabled
        self.type = type