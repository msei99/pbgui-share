import subprocess
from pathlib import Path, PurePath
from time import sleep
from datetime import datetime
import traceback
from MySQLDatabase import Database
from User import Users
import configparser

class PBGShare():
    def __init__(self):
        self.load_ini()
        self.db = Database()
        self.users = Users()

    def update_db(self):
        PBGUI_DB = Path(f'{self.pbgdir}/data/pbgui.db')
        for user in self.users:
            if user.name == "hl_manicpt":
                print(f'{datetime.now().isoformat(sep=" ", timespec="seconds")} Update pbgui-share db {user.name}')
                self.db.copy_user_mysql(f'{PBGUI_DB}', user)
                self.db.add_ohlcv(user)

    def update_git(self):
        cmd = ['git', 'add', 'api-keys.json']
        subprocess.run(cmd, text=True)
        cmd = ['git', 'commit', '-m', f'Update pbgui-share.db {datetime.now().isoformat(sep=" ", timespec="seconds")}']
        subprocess.run(cmd, text=True)
        cmd = ['git', 'push', f'https://{self.git_user}:{self.git_token}@{self.git_url}']
        subprocess.run(cmd, text=True)

    def load_ini(self):
        pb_config = configparser.ConfigParser()
        pb_config.read('pbgui-share.ini')
        self.pbgdir = pb_config.get("main", "pbgdir")
        self.git_user = pb_config.get("git", "user")
        self.git_url = pb_config.get("git", "url")
        self.git_token = pb_config.get("git", "token")
    
def main():
    print(f'{datetime.now().isoformat(sep=" ", timespec="seconds")} Start: PBData')
    pbdata = PBGShare()
    while True:
        try:
            pbdata.update_db()
            # pbdata.update_git()
            sleep(300)
            pbdata.users.load()
        except Exception as e:
            print(f'Something went wrong, but continue {e}')
            traceback.print_exc()

if __name__ == '__main__':
    main()