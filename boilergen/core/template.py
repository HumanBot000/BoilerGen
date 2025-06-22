class Template:
    def __init__(self,id:str, label: str,dependencies: list[str], config: dict[str,any]):
        self.id = id
        self.label = label
        self.dependencies = dependencies
        self.config = config