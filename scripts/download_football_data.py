"""
批量下载 football-data.co.uk 全部CSV数据
按 国家/联赛/赛季 分类保存到 football-data/ 目录
"""
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# 联赛定义: (国家, 联赛名, 联赛码, 起始赛季, 最大赛季数)
LEAGUES = [
    # 英格兰
    ("England", "Premier_League", "E0", 1993, 33),
    ("England", "Championship", "E1", 2001, 25),
    ("England", "League_One", "E2", 2004, 22),
    ("England", "League_Two", "E3", 2004, 22),
    ("England", "National_League", "EC", 2004, 22),
    # 苏格兰
    ("Scotland", "Premiership", "SC0", 1997, 29),
    ("Scotland", "Championship", "SC1", 1997, 29),
    ("Scotland", "League_One", "SC2", 1997, 29),
    ("Scotland", "League_Two", "SC3", 1997, 29),
    # 德国
    ("Germany", "Bundesliga", "D1", 1993, 33),
    ("Germany", "2_Bundesliga", "D2", 1997, 29),
    # 意大利
    ("Italy", "Serie_A", "I1", 1993, 33),
    ("Italy", "Serie_B", "I2", 1997, 29),
    # 西班牙
    ("Spain", "La_Liga", "SP1", 1993, 33),
    ("Spain", "Segunda", "SP2", 1997, 29),
    # 法国
    ("France", "Ligue_1", "F1", 1993, 33),
    ("France", "Ligue_2", "F2", 1997, 29),
    # 其他
    ("Netherlands", "Eredivisie", "N1", 1997, 29),
    ("Belgium", "Jupiler_Pro_League", "B1", 1997, 29),
    ("Portugal", "Primeira_Liga", "P1", 1997, 29),
    ("Turkey", "Super_Lig", "T1", 1997, 29),
    ("Greece", "Super_League", "G1", 1997, 29),
]

BASE_URL = "https://www.football-data.co.uk/mmz4281"
OUTPUT_DIR = Path(__file__).parent.parent / "football-data"
MAX_RETRIES = 2
REQUEST_DELAY = 0.3  # 请求间隔，避免被封
MAX_WORKERS = 5

STATS = {"success": 0, "failed": 0, "skipped": 0, "total": 0}


def season_to_code(start_year: int) -> str:
    """1993 -> '9394'"""
    return f"{start_year % 100:02d}{(start_year + 1) % 100:02d}"


def download_csv(url: str, filepath: Path) -> bool:
    """下载单个CSV文件"""
    if filepath.exists():
        STATS["skipped"] += 1
        return True

    for attempt in range(MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
                # 检查是否为有效CSV（不是HTML错误页）
                if len(data) < 200 or data[:20].startswith(b"<!DOCTYPE") or data[:20].startswith(b"<html"):
                    return False
                filepath.parent.mkdir(parents=True, exist_ok=True)
                with open(filepath, 'wb') as f:
                    f.write(data)
                STATS["success"] += 1
                return True
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return False  # 这个赛季没有数据
            if attempt < MAX_RETRIES:
                time.sleep(1)
        except Exception:
            if attempt < MAX_RETRIES:
                time.sleep(1)

    STATS["failed"] += 1
    return False


def download_task(args):
    """单个下载任务（线程池用）"""
    url, filepath, progress = args
    success = download_csv(url, filepath)
    if success:
        print(f"  {progress}", end="\r", flush=True)
    return success


def main():
    print("=" * 60)
    print("  football-data.co.uk 全量数据下载")
    print("=" * 60)
    print(f"  联赛数: {len(LEAGUES)}")
    print(f"  输出目录: {OUTPUT_DIR}")
    print()

    all_tasks = []

    for country, league_name, league_code, start_year, num_seasons in LEAGUES:
        country_dir = OUTPUT_DIR / country
        league_dir = country_dir / league_name

        seasons_exist = 0
        for i in range(num_seasons):
            sy = start_year + i
            season_code = season_to_code(sy)
            url = f"{BASE_URL}/{season_code}/{league_code}.csv"
            filename = f"{season_code}_{league_code}.csv"
            filepath = league_dir / filename

            all_tasks.append((url, filepath, f"{country}/{league_name}/{filename}"))
            STATS["total"] += 1

    print(f"  待下载文件: {STATS['total']}")
    print(f"  工作线程: {MAX_WORKERS}")
    print()

    # 顺序下载（对服务器友好，避免并发被封）
    completed = 0
    for url, filepath, label in all_tasks:
        success = download_csv(url, filepath)
        completed += 1
        if completed % 50 == 0 or completed == STATS["total"]:
            print(f"  进度: {completed}/{STATS['total']}  "
                  f"(成功: {STATS['success']}, 跳过: {STATS['skipped']}, "
                  f"失败: {STATS['failed']})", flush=True)
        if completed % 5 == 0:
            time.sleep(REQUEST_DELAY)  # 每5个请求暂停一下

    # 汇总
    print()
    print("=" * 60)
    print("  下载完成!")
    print(f"  成功: {STATS['success']}")
    print(f"  已跳过 (已存在): {STATS['skipped']}")
    print(f"  失败: {STATS['failed']}")
    print(f"  合计: {STATS['total']}")
    print("=" * 60)

    # 生成目录树摘要
    print("\n  数据目录结构:")
    for country_dir in sorted(OUTPUT_DIR.iterdir()):
        if country_dir.is_dir():
            total_files = sum(1 for _ in country_dir.rglob("*.csv"))
            total_size = sum(f.stat().st_size for f in country_dir.rglob("*.csv"))
            size_mb = total_size / (1024 * 1024)
            print(f"  {country_dir.name}/")
            for league_dir in sorted(country_dir.iterdir()):
                if league_dir.is_dir():
                    n = len(list(league_dir.glob("*.csv")))
                    print(f"    {league_dir.name}/  ({n} 个赛季)")
            print(f"    总计: {total_files} 文件, {size_mb:.1f} MB")
            print()


if __name__ == "__main__":
    main()
