class PostgresConnection:
    def __init__(
            self,
            host,
            port='5432',
            username='postgres',
            password='postgres',
            dbname='postgres'):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.dbname = dbname

    def connect(self):
        from sqlalchemy import create_engine
        return create_engine(self.__str__())

    def __str__(self):
        return f'postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.dbname}'
