# Дисклеймер

Все ниже - псевдокод, очень похожий на рабочий, понятно, что между потоками нужно использовать мьютексы для блокировки, а кафка вообще байты возвращает, а не строку, но это все нужно для того, чтобы показать как будет происходить работа с ивентами 

# Ивенты
Ивент - это класс с типом ивента и информацией ивента

Ивенты передаются через сообщения, для удобства определения типа ивента, предлагаю первые четыре символа сообщения отводить на тип ивента, тогда сообщения ивентов имееют вид `<event_type_prefix> <event_data>`

Тип ивента будет представляться enum'ом, каждому варианту будет соответсвовать его представление в виде префикса сообщения:

```py
class EventType(Enum):
    Invalid = 'erro'
    TrendData = 'trda'
    Scalek8s = 'sck8'
    ...
```

Для упрощения работы с этим enum'ом, я завел новый класс с двумя словарями:
- словарь, в котором ключ - объект enum'а, а значение - префикс сообщения этого типа ивента
- словарь, в котором ключ - префикс сообщения типа ивента, а значение - объект enum'а с этим префиксом

Задаются эти два словаря автоматически *(с помощью магии питона)*:

```py
_event_type_members = EventType._member_map_.values()
class EventTypeConstants:
    event_type_to_prefix = {} # {<EventType.Invalid: 'erro'>: 'erro', <EventType.TrendData: 'trda'>: 'trda', ...}
    prefix_to_event_type = {} # {'erro': <EventType.Invalid: 'erro'>, 'trda': <EventType.TrendData: 'trda'>, ...}

    for enum in _event_type_members:
        event_type_to_prefix[enum] = enum.value
        prefix_to_event_type[enum.value] = enum
```

Рассмотрим конструирование ивентов из сообщений кафки:

```py
class Event:
    def __init__(self, type: EventType, data: Union[str, TrendData]):
        self.type = type
        self.data = data

class EventFromMessage(Event):
    def __init__(self, kafka_message: str):
        prefix = kafka_message[:4]
        data = kafka_message[5:]

        try:
            event_type = EventTypeConstants.prefix_to_event_type[prefix]
        except:
            event_type = EventType.Invalid

        match event_type:
            case EventType.TrendData:
                data = TrendDataFromStr(data)
            case EventType.Scalek8s:
                data = ScaleDataFromStr(data)
            ...
            case _:
                data = f'Error: got invalid message: {kafka_message}'

        return super().__init__(event_type, data)
```

Получается, для каждого класса, что передается между ивентами нужно написать метод десериализации

Рассмотрим превращение ивентов в строку, тут нам надо написать метод сериализации (`__str__`):

```py
class Event:
    ...
    def __str__(self) -> str:
        return f'{EventTypeConstants.event_type_to_prefix[self.type]} {self.data}'
```

> На самом деле мы бы могли и десериализацию без свитч кейсов написать, но тогда нужно писать общий класс `Data`, который хз пока нужен или нет

Итого сами ивенты у нас есть, их можно сериализовывать в строки и десериализовывать из строк, осталось написать сам механизм передачи по кафке

# Кафка

Я хочу сразу чтобы мои новые классы внутри хранили именно ивенты, а не сообщения с кафки.

Здесь все просто: создадим два класса - на считывание (`KafkaEventReader`) и на запись (`KafkaEventWriter`)

## Считывание

```py
class KafkaEventReader:
    '''
    Класс, который считывает сообщения с кафки и сохраняет их в виде ивентов
    '''

    def __init__(self, kafka_config: KafkaConfig):
        '''
        Подписка к кафке с помощью конфига
        '''
        self.consumer = KafkaConsumer(...)
        self.running = True
        self.events = Queue()

    async def read_events(self):
        '''
        Считывание сообщений от кафки, превращение их в ивенты, сохранение в очередь ивентов
        Запущен на отдельном потоке для постоянного считывания новых сообщений
        '''
        while self.running:
            message = self.consumer.consume()
            if message is not None:
                self.events.put(EventFromMessage(message))

    def get_event(self) -> Optional[EventFromMessage]:
        '''
        Возвращение первого ивента из очереди ивентов, если он есть
        '''
        if not self.events.empty():
            return self.events.get()
        return None

    def release(self):
        '''
        Отключение от кафки
        '''
        self.running = False
        self.consumer.close()
```

То есть `read_events()` запущен постоянно, он сохраняет ивенты в очередь, а `get_event()` иногда запрашивает первый элемент в очереди

## Запись

Тут просто в кафку отправляется по адресу из конфига сообщение конструированное из ивента

```py
class KafkaEventWriter:
    '''
    Класс, который превращает ивенты в сообщения и отправляет их в кафку
    '''

    def __init__(self, kafka_config: KafkaConfig):
        '''
        Инициализация класса - подключение к кафке с помощью конфига
        '''
        self.producer = KafkaProducer(...)

    def send_event(self, event: Event):
        '''
        Отправка ивента превращенного в сообщение
        '''
        message = str(event)
        self.producer.send(message)
        
    def close(self):
        '''
        Отключение от кафки
        '''
        pass
```
