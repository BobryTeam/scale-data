class ScaleData:
    def __init__(self, replica_count: int):
        '''
        Инициализация класса
        '''
        self.replica_count = replica_count

    def __str__(self) -> str:
        '''
        Превращает скейл дату в строку
        '''
        return str(self.replica_count)

class ScaleDataFromStr(ScaleData):
    def __init__(self, string_data: str):
        '''
        Инициализация класса из строки
        '''
        return super().__init__(int(string_data))
