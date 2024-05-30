class ScaleData:
    def __init__(self, replica_coefficient: float):
        '''
        Инициализация класса
        '''
        self.replica_coefficient: float = replica_coefficient

    def __str__(self) -> str:
        '''
        Превращает скейл дату в строку
        '''
        return str(self.replica_coefficient)

class ScaleDataFromStr(ScaleData):
    def __init__(self, string_data: str):
        '''
        Инициализация класса из строки
        '''
        return super().__init__(float(string_data))
