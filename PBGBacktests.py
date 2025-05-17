from pathlib import Path
from time import sleep
import sys
from io import TextIOWrapper
import traceback
from User import Users
import configparser
from pathlib import Path, PurePath
import subprocess
import shutil
import json
from datetime import datetime, timedelta
import glob
import pandas as pd
import plotly.graph_objects as go

class PBGBacktests():
    def __init__(self):
        self.backtestsdir = None
        self.pbgdir = None
        self.pb7dir = None
        self.pb7venv = None
        self.pb6dir = None
        self.pb6venv = None
        self.pbgdir = None
        self.git_user = None
        self.git_email = None
        self.git_path = None
        self.git_token = None
        self.ed = None
        self.be = None
        self.fills = None
        self.load_ini()
        self.users = Users()

    def update_backtests(self):
        update = False
        if not Path(self.backtestsdir).exists():
            Path(self.backtestsdir).mkdir(parents=True)
        for user in self.users:
            if user.backtests:
                update = True
                for year in range(2020, datetime.now().year + 1):
                    year = str(year)
                    if Path(f'{self.backtestsdir}/{user.name}_{year}.png').exists():
                        if year != datetime.now().strftime('%Y'):
                            continue
                    print(f'{datetime.now().isoformat(sep=" ", timespec="seconds")} Backtest {user.name} {year}')
                    self.backtest(user, year)
                print(f'{datetime.now().isoformat(sep=" ", timespec="seconds")} Backtests {user.name} all')
                self.backtest(user, 'all')
        if update:
            print(f'{datetime.now().isoformat(sep=" ", timespec="seconds")} Update git')
            self.update_git()
    
    def load_git_url(self):
        git_config = configparser.ConfigParser()
        git_config_file = Path(f"{self.git_path}/.git/config")
        if not git_config_file.exists():
            print(f'No git config found')
            return
        url = ""
        git_config.read(git_config_file)
        if git_config.has_section('remote "origin"'):
            if git_config.has_option('remote "origin"', 'url'):
                remote_url = git_config.get('remote "origin"', 'url')
                if url.startswith("http://"):
                    url = remote_url.replace("http://", f"http://{self.git_token}@")
                if remote_url.startswith('https://'):
                    url = remote_url.replace("https://", f"https://{self.git_token}@")
        return url
            
    def update_git(self):
        url = self.load_git_url()
        if not url:
            print(f'No git url found')
            return
        try:
            # Configure username and email
            cmd = ["git", "-C", self.git_path, "config", "user.name", self.git_user]
            try:
                result = subprocess.run(cmd, capture_output=True, check=True, text=True)
            except subprocess.CalledProcessError as e:
                print(f"Error configuring username for {self.my_archive}: {e.stderr}")
                return
            cmd = ["git", "-C", self.git_path, "config", "user.email", self.git_email]
            try:
                result = subprocess.run(cmd, capture_output=True, check=True, text=True)
            except subprocess.CalledProcessError as e:
                print(f"Error configuring email for {self.my_archive}: {e.stderr}")
                return

            cmd = ['git', '-C', self.git_path, 'add', '-A']
            result = subprocess.run(cmd, capture_output=True, cwd=self.pbgdir, text=True, start_new_session=True)
            if result.returncode != 0:
                print(f'Error in git add: {result.stderr}')
                print(f'{result.stdout}')
                return

            formatted_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cmd = ['git', '-C', self.git_path, 'commit', '-m', f'update backtests {formatted_time}']
            result = subprocess.run(cmd, capture_output=True, cwd=self.pbgdir, text=True, start_new_session=True)
            if result.returncode != 0:
                print(f'Error in git commit: {result.stderr}')
                print(f'{result.stdout}')
                return

            cmd = ['git', '-C', self.git_path, 'pull']
            result = subprocess.run(cmd, capture_output=True, cwd=self.pbgdir, text=True, start_new_session=True)
            if result.returncode != 0:
                print(f'Error in git pull: {result.stderr}')
                print(f'{result.stdout}')
                return
            cmd = ['git', '-C', self.git_path, 'push', url]
            result = subprocess.run(cmd, capture_output=True, cwd=self.pbgdir, text=True, start_new_session=True)
            if result.returncode != 0:
                print(f'Error in git push: {result.stderr}')
                print(f'{result.stdout}')
                return

        except Exception as e:
            print(f'Exception occurred during git operations: {e}')
            traceback.print_exc()
    
    def backtest(self, user, year : str):
        # remove old backtest
        backtest = Path.cwd() / 'backtests' / f'{user.name}_{year}'
        if backtest.exists():
            shutil.rmtree(backtest)
        if Path(f'{self.pbgdir}/data/run_v7/{user.name}/config.json').exists():
            config = self.create_backtest_json(user, year)
            cmd = [self.pb7venv, '-u', PurePath(f'{self.pb7dir}/src/backtest.py'), str(PurePath(f'{config}'))]
            result = subprocess.run(cmd, capture_output=True, cwd=self.pb7dir, text=True, start_new_session=True)
        elif Path(f'{self.pbgdir}/data/multi/{user.name}/multi.hjson').exists():
            if user.name == 'bitget_UNI_MEME':
                multi = Path(f'{self.pbgdir}/data/bt_multi/{user.name}/backtest.hjson')
            elif user.name == 'hl_manicpt':
                multi = Path(f'{self.pbgdir}/data/bt_multi/{user.name}/backtest.hjson')
            else:
                multi = Path(f'{self.pbgdir}/data/multi/{user.name}/multi.hjson')
            base_dir = Path.cwd() / 'backtests' / f'{user.name}_{year}'
            if year == 'all':
                sd = "2020-01-01"
                # end_date = today - 1 day
                ed = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            elif year == '2020':
                sd = "2020-01-01"
                ed = "2020-12-31"
            elif year == '2021':
                sd = "2021-01-01"
                ed = "2021-12-31"
            elif year == '2022':
                sd = "2022-01-01"
                ed = "2022-12-31"
            elif year == '2023':
                sd = "2023-01-01"
                ed = "2023-12-31"
            elif year == '2024':
                sd = "2024-01-01"
                ed = "2024-12-31"
            elif year == '2025':
                sd = "2025-01-01"
                ed = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            self.ed = ed
            if user.exchange not in ['binance', 'bybit']:
                exchange = 'bybit'
            else:
                exchange = user.exchange
            cmd = [self.pb6venv, '-u', PurePath(f'{self.pb6dir}/backtest_multi.py'), '-bc', str(PurePath(f'{multi}')), '-bd', str(PurePath(f'{base_dir}')), '-sd', sd, '-ed', ed, '-sb', '1000', '-e', exchange]
            result = subprocess.run(cmd, capture_output=True, cwd=self.pb6dir, text=True, start_new_session=True)
        else:
            print(f'No config found for {user.name}')
            return
        if result.returncode == 0:
            glob_be = f'{backtest}/**/balance_and_equity.csv'
            be = glob.glob(glob_be, recursive=True)
            if not be:
                glob_be = f'{backtest}/**/stats.csv'
                be = glob.glob(glob_be, recursive=True)
            if be:
                self.load_be(be[0])
                if self.be is not None:
                    self.save_chart_be(f'{user.name}_{year}')
            glob_fills = f'{backtest}/**/fills.csv'
            fills = glob.glob(glob_fills, recursive=True)
            if fills:
                self.load_fills(fills[0])
                if self.fills is not None:
                    self.save_chart_symbol(f'{user.name}_{year}')
        else:
            # create a png with text "Not enough data for year {year}"
            fig = go.Figure()
            fig.add_annotation(text=f'Not enough data for year {year}', showarrow=False)
            fig.update_layout(template='plotly_dark', width=1920, height=1080)
            fig.write_image(f'{self.backtestsdir}/{user.name}_{year}.png')
            fig.write_image(f'{self.backtestsdir}/{user.name}_{year}_symbol.png')

    # Create Chart with plotly
    def save_chart_be(self, file_name):
        if self.be is not None:
            fig = go.Figure()
            fig.update_layout(yaxis_title='Balance')
            fig.add_trace(go.Scatter(x=self.be['time'], y=self.be['equity'], name="equity", line=dict(width=0.75)))
            fig.add_trace(go.Scatter(x=self.be['time'], y=self.be['balance'], name="balance", line=dict(width=2.5)))
            fig.update_layout(yaxis_title='Balance', height=800)
            fig.update_xaxes(showgrid=True, griddash="dot")
            formatted_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            fig.update_layout(title_text=f'{file_name} {formatted_time}', title_x=0.5)
            # save chart
            fig.update_layout(template='plotly_dark', width=1920, height=1080)
            fig.write_image(f'{self.backtestsdir}/{file_name}.png')

    # Create Symbol Chart with plotly
    def save_chart_symbol(self, file_name):
        if self.fills is not None:
            fig = go.Figure()
            if "symbol" in self.fills:
                coin_or_symbol = "symbol"
            elif "coin" in self.fills:
                coin_or_symbol = "coin"
            for symbol in self.fills[coin_or_symbol].unique():
                symbol_df = self.fills[self.fills[coin_or_symbol] == symbol].copy()
                symbol_df["sym_pnl"] = symbol_df["pnl"].cumsum()
                fig.add_trace(go.Scatter(x=symbol_df['time'], y=symbol_df['sym_pnl'], name=symbol))
            # fig.update_layout(yaxis_title='PnL', height=800, )
            fig['data'][0]['showlegend'] = True
            fig.update_xaxes(showgrid=True, griddash="dot")
            # save chart
            fig.update_layout(template='plotly_dark', width=1920, height=1080)
            fig.write_image(f'{self.backtestsdir}/{file_name}_symbol.png')

    def load_be(self, be):
        if Path(be).exists():
            self.be = pd.read_csv(be)
            timestamp = datetime.strptime(self.ed, '%Y-%m-%d').timestamp()
            start_time = timestamp - (self.be.iloc[:, 0].iloc[-1] * 60)
            self.be['time'] = datetime.fromtimestamp(start_time) + pd.to_timedelta(self.be.iloc[:, 0], unit='m')

    def load_fills(self, fills):
        if Path(fills).exists():
            self.fills = pd.read_csv(fills)
            timestamp = datetime.strptime(self.ed, '%Y-%m-%d').timestamp()
            start_time = timestamp - (self.fills['minute'].iloc[-1] * 60)
            self.fills['time'] = datetime.fromtimestamp(start_time) + pd.to_timedelta(self.fills['minute'], unit='m')

    def create_backtest_hjson(self, user, year : str):
        # copy config from user to backtests
        config_src = Path(f'{self.pbgdir}/data/multi/{user.name}')
        #config_dst = cwd + backtest
        config_dst_dir = Path.cwd() / 'backtests'
        if not config_dst_dir.exists():
            config_dst_dir.mkdir()
        config_dst = config_dst_dir / f'{user.name}_{year}'
        shutil.copytree(config_src, config_dst)
        # update config with backtest url
        config_multi = config_dst / 'multi.hjson'
        with open(config_multi, 'r') as f:
            config = hjson.load(f)
    
    def create_backtest_json(self, user, year : str):
        # copy config from user to backtests
        config_src = Path(f'{self.pbgdir}/data/run_v7/{user.name}/config.json')
        #config_dst = cwd + backtest
        config_dst_dir = Path.cwd() / 'backtests'
        if not config_dst_dir.exists():
            config_dst_dir.mkdir()
        config_dst = config_dst_dir / f'{user.name}_{year}.json'
        shutil.copyfile(config_src, config_dst)
        # update config with backtest url
        with open(config_dst, 'r') as f:
            config = json.load(f)
        # copy config from remote when dynamic_ignore is not disabled
        if "pbgui" in config:
            if "dynamic_ignore" in config["pbgui"]:
                enabled_on = config["pbgui"]["enabled_on"]
                if enabled_on != "disabled":
                    approved_coins_path = Path(f'{self.pbgdir}/data/remote/run_v7_{enabled_on}/{user.name}/approved_coins.json')
                    ignored_coins_path = Path(f'{self.pbgdir}/data/remote/run_v7_{enabled_on}/{user.name}/ignored_coins.json')
                    if approved_coins_path.exists():
                        with open(approved_coins_path, 'r') as f:
                            approved_coins = json.load(f)
                        config['live']['approved_coins'] = approved_coins
                    if ignored_coins_path.exists():
                        with open(ignored_coins_path, 'r') as f:
                            ignored_coins = json.load(f)
                        config['live']['ignored_coins'] = ignored_coins
        config['backtest']["base_dir"] = str(config_dst_dir / f'{user.name}_{year}')
        if year == 'all':
            config['backtest']["start_date"] = "2020-01-01"
            # end_date = today - 1 day
            config['backtest']["end_date"] = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        elif year == '2020':
            config['backtest']["start_date"] = "2020-01-01"
            config['backtest']["end_date"] = "2020-12-31"
        elif year == '2021':
            config['backtest']["start_date"] = "2021-01-01"
            config['backtest']["end_date"] = "2021-12-31"
        elif year == '2022':
            config['backtest']["start_date"] = "2022-01-01"
            config['backtest']["end_date"] = "2022-12-31"
        elif year == '2023':
            config['backtest']["start_date"] = "2023-01-01"
            config['backtest']["end_date"] = "2023-12-31"
        elif year == '2024':
            config['backtest']["start_date"] = "2024-01-01"
            config['backtest']["end_date"] = "2024-12-31"
        elif year == '2025':
            config['backtest']["start_date"] = "2025-01-01"
            config['backtest']["end_date"] = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        self.ed = config['backtest']["end_date"]
        if user.exchange not in ['binance', 'bybit']:
            config['backtest']["exchange"] = "binance"
        else:
            config['backtest']["exchanges"] = [user.exchange]
        config['backtest']["combine_ohlcvs"] = False
        config['backtest']["starting_balance"] = 1000
        # save config
        with open(config_dst, 'w') as f:
            json.dump(config, f, indent=4)
        return config_dst

    def load_ini(self):
        pb_config = configparser.ConfigParser()
        pb_config.read('pbgui-share.ini')
        if pb_config.has_section("main"):
            if pb_config.has_option("main", "pbgdir"):
                self.pbgdir = pb_config.get("main", "pbgdir")
            if pb_config.has_option("main", "backtestsdir"):
                self.backtestsdir = pb_config.get("main", "backtestsdir")
            if pb_config.has_option("main", "pb7dir"):
                self.pb7dir = pb_config.get("main", "pb7dir")
            if pb_config.has_option("main", "pb7venv"):
                self.pb7venv = pb_config.get("main", "pb7venv")
            if pb_config.has_option("main", "pb6dir"):
                self.pb6dir = pb_config.get("main", "pb6dir")
            if pb_config.has_option("main", "pb6venv"):
                self.pb6venv = pb_config.get("main", "pb6venv")
            if pb_config.has_option("main", "git_user"):
                self.git_user = pb_config.get("main", "git_user")
            if pb_config.has_option("main", "git_email"):
                self.git_email = pb_config.get("main", "git_email")
            if pb_config.has_option("main", "git_token"):
                self.git_token = pb_config.get("main", "git_token")
            if pb_config.has_option("main", "git_path"):
                self.git_path = pb_config.get("main", "git_path")
    
def main():
    pbbacktests = PBGBacktests()
    if not pbbacktests.pbgdir:
        print(f'pbgdir is not defined in pbgui-share.ini')
        return
    if not pbbacktests.backtestsdir:
        print(f'backtestsdir is not defined in pbgui-share.ini')
        return
    if not pbbacktests.pb7dir:
        print(f'pb7dir is not defined in pbgui-share.ini')
        return
    if not pbbacktests.pb7venv:
        print(f'pb7venv is not defined in pbgui-share.ini')
        return
    if not pbbacktests.pb6dir:
        print(f'pb6dir is not defined in pbgui-share.ini')
        return
    if not pbbacktests.pb6venv:
        print(f'pb6venv is not defined in pbgui-share.ini')
        return
    # Init logfile
    logfile = Path(f'PBGBacktests.log')
    # sys.stdout = TextIOWrapper(open(logfile,"ab",0), write_through=True)
    # sys.stderr = TextIOWrapper(open(logfile,"ab",0), write_through=True)
    print(f'{datetime.now().isoformat(sep=" ", timespec="seconds")} Start: PBGBacktests')
    while True:
        try:
            if logfile.exists():
                if logfile.stat().st_size >= 10485760:
                    logfile.replace(f'{str(logfile)}.old')
                    sys.stdout = TextIOWrapper(open(logfile,"ab",0), write_through=True)
                    sys.stderr = TextIOWrapper(open(logfile,"ab",0), write_through=True)
            pbbacktests.update_backtests()
            now = datetime.now()
            next_run = (now + timedelta(days=1)).replace(hour=4, minute=0, second=0, microsecond=0)
            sleep_seconds = (next_run - now).total_seconds()
            sleep_hours, rem = divmod(sleep_seconds, 3600)
            sleep_minutes, sleep_seconds = divmod(rem, 60)
            print(f'{datetime.now().isoformat(sep=" ", timespec="seconds")} Sleep until {next_run.isoformat(sep=" ", timespec="seconds")} for {int(sleep_hours)} hours, {int(sleep_minutes)} minutes, and {int(sleep_seconds)} seconds')
            sleep(next_run.timestamp() - now.timestamp())
            pbbacktests.users.load()
        except Exception as e:
            print(f'Something went wrong, but continue {e}')
            traceback.print_exc()

if __name__ == '__main__':
    main()