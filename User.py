import json
from pathlib import Path

class User:
    def __init__(self):
        self._name = None
        self._exchange = None
        self._url = None
    
    @property
    def name(self): return self._name
    @property
    def exchange(self): return self._exchange
    @property
    def url(self): return self._url

    @name.setter
    def name(self, new_name):
        self._name = new_name
    @exchange.setter
    def exchange(self, new_exchange):
        self._exchange = new_exchange
    @url.setter
    def url(self, new_url):
        self._url = new_url


class Users:
    def __init__(self):
        self.users = []
        self.index = 0
        self.api_path = f'api-keys.json'
        self.load()
    
    def __iter__(self):
        return iter(self.users)

    def __next__(self):
        if self.index > len(self.users):
            raise StopIteration
        self.index += 1
        return next(self)
    
    def list(self):
        return list(map(lambda c: c.name, self.users))
    
    def default(self):
        if self.users:
            return self.users[0].name
        else:
            return None

    def has_user(self, user: User):
        for u in self.users:
            if u != user and u.name == user.name:
                return True
        return False

    def remove_user(self, name: str):
        for user in self.users:
            if user.name == name:
                self.users.remove(user)
                self.save()

    def find_user(self, name: str):
        for user in self.users:
            if user.name == name:
                return user

    def find_exchange(self, name: str):
        for user in self.users:
            if user.name == name:
                return user.exchange

    def find_exchange_user(self, exchange: str):
        for user in self.users:
            if user.exchange == exchange:
                return user.name

    def load(self):
        try:
            with Path(self.api_path).open(encoding="UTF-8") as f:
                users = json.load(f)
        except Exception as e:
            print(f'{self.api_path} is corrupted {e}')
            return
        self.users = []
        for user in users:
            if "exchange" in users[user]:
                my_user = User()
                my_user.name = user
                my_user.exchange = users[user]["exchange"]
                if "url" in users[user]:
                    my_user.url = users[user]["url"]    
                self.users.append(my_user)
        self.users.sort(key=lambda x: x.name)

    def save(self):
        save_users = {}
        for user in self.users:
            save_users[user.name] = ({
                        "exchange": user.exchange
                    })
            if user.url:
                save_users[user.name]["url"] = user.url
        with Path(f'{self.api_path}').open("w", encoding="UTF-8") as f:
            json.dump(save_users, f, indent=4)

def main():
    print("Don't Run this Class from CLI")

if __name__ == '__main__':
    main()
