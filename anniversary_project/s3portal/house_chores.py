import abc


class HouseChore(abc.ABC):
    """
    The abstract class for defining a house chore instance. All house chore instances will be executed as part of a
    local house kepping routine
    """
    @abc.abstractmethod
    def execute(self):
        raise NotImplementedError('execution not defined')

    @abc.abstractmethod
    def name(self):
        raise NotImplementedError('house chore name not defined')


