from abc import ABC, abstractmethod


class ILogger(ABC):
    @abstractmethod
    def debug(self, message: str, **kwargs) -> None:
        pass

    @abstractmethod
    def info(self, message: str, **kwargs) -> None:
        pass

    @abstractmethod
    def success(self, message: str, **kwargs) -> None:
        pass

    @abstractmethod
    def warn(self, message: str, **kwargs) -> None:
        pass

    @abstractmethod
    def error(self, message: str, **kwargs) -> None:
        pass
