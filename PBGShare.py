from pathlib import Path
from time import sleep
import sys
from io import TextIOWrapper
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
            print(f'{datetime.now().isoformat(sep=" ", timespec="seconds")} Update pbgui-share db {user.name}')
            self.db.copy_user_mysql(f'{PBGUI_DB}', user)
            self.db.add_ohlcv(user)

    def load_ini(self):
        pb_config = configparser.ConfigParser()
        pb_config.read('pbgui-share.ini')
        self.pbgdir = pb_config.get("main", "pbgdir")
    
def main():
    logfile = Path(f'PBGShare.log')
    sys.stdout = TextIOWrapper(open(logfile,"ab",0), write_through=True)
    sys.stderr = TextIOWrapper(open(logfile,"ab",0), write_through=True)
    print(f'{datetime.now().isoformat(sep=" ", timespec="seconds")} Start: PBData')
    pbdata = PBGShare()
    while True:
        try:
            if logfile.exists():
                if logfile.stat().st_size >= 10485760:
                    logfile.replace(f'{str(logfile)}.old')
                    sys.stdout = TextIOWrapper(open(logfile,"ab",0), write_through=True)
                    sys.stderr = TextIOWrapper(open(logfile,"ab",0), write_through=True)
            pbdata.update_db()
            print(f'{datetime.now().isoformat(sep=" ", timespec="seconds")} Sleep for 5 minutes')
            sleep(300)
            pbdata.users.load()
        except Exception as e:
            print(f'Something went wrong, but continue {e}')
            traceback.print_exc()

if __name__ == '__main__':
    main()