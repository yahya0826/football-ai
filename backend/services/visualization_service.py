"""
可视化服务 - xG曲线、热力图、射门分布图
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mplsoccer import Pitch, VerticalPitch
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import base64
from io import BytesIO
import json

class VisualizationService:
    """可视化服务"""

    def __init__(self, output_dir: str = "static/images"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _events_to_vertical_coords(self, events: pd.DataFrame) -> pd.DataFrame:
        """转换事件坐标到垂直方向"""
        if events.empty or 'location' not in events.columns:
            return events

        events = events.copy()
        # StatsBomb坐标是[0,100] x [0,100]，需要转换
        # x保持不变，y需要翻转（0在底部）
        def transform_coord(loc):
            if isinstance(loc, (list, tuple)) and len(loc) >= 2:
                return [loc[0], 100 - loc[1]]
            return loc

        if 'location' in events.columns:
            events['location'] = events['location'].apply(transform_coord)
        return events

    def calculate_xg(self, shots: pd.DataFrame) -> pd.DataFrame:
        """计算xG值（简化模型）"""
        if shots.empty:
            return shots

        shots = shots.copy()

        # xG模型参数（基于位置）
        for idx, shot in shots.iterrows():
            location = shot.get('location', [50, 50])
            if isinstance(location, (list, tuple)) and len(location) >= 2:
                x, y = location[0], location[1]

                # 距离球门的距离（假设球门在x=100）
                distance = 100 - x

                # 基本xG = 1 / (1 + exp(-(距离因子)))
                distance_factor = np.exp(-0.07 * distance)

                # 角度因子
                y_normalized = abs(y - 50) / 50
                angle_factor = 1 - 0.3 * y_normalized

                # 使用StatsBomb的xG（如果有）或计算
                if pd.notna(shot.get('shot_statsbomb_xg')):
                    shots.at[idx, 'xg'] = shot['shot_statsbomb_xg']
                else:
                    shots.at[idx, 'xg'] = distance_factor * angle_factor
            else:
                shots.at[idx, 'xg'] = 0.05

        return shots

    def generate_xg_chart(self, match_id: int, events: pd.DataFrame) -> Optional[str]:
        """生成xG时间曲线图"""
        try:
            shots = events[events['type'] == 'Shot'].copy()
            if shots.empty:
                return None

            shots = self.calculate_xg(shots)

            # 按时间累加xG
            shots_sorted = shots.sort_values('minute')
            home_xg = 0
            away_xg = 0

            xg_timeline = []
            for _, shot in shots_sorted.iterrows():
                team = shot['team']
                xg = shot.get('xg', 0.05)
                minute = shot.get('minute', 0)

                if team == shots_sorted.iloc[0]['team']:
                    home_xg += xg
                else:
                    away_xg += xg

                xg_timeline.append({
                    'minute': minute,
                    'home_xg': home_xg,
                    'away_xg': away_xg,
                    'team': team
                })

            # 绘制xG曲线
            fig, ax = plt.subplots(figsize=(12, 6))

            minutes = [0] + [d['minute'] for d in xg_timeline]
            home_values = [0] + [d['home_xg'] for d in xg_timeline]
            away_values = [0] + [d['away_xg'] for d in xg_timeline]

            ax.step(minutes, home_values, where='post', label='Home xG', linewidth=2, color='#2ecc71')
            ax.step(minutes, away_values, where='post', label='Away xG', linewidth=2, color='#e74c3c')

            ax.fill_between(minutes, home_values, step='post', alpha=0.3, color='#2ecc71')
            ax.fill_between(minutes, away_values, step='post', alpha=0.3, color='#e74c3c')

            ax.set_xlabel('Minute', fontsize=12)
            ax.set_ylabel('Expected Goals (xG)', fontsize=12)
            ax.set_title(f'Match {match_id} - xG Timeline', fontsize=14, fontweight='bold')
            ax.legend(loc='upper left')
            ax.grid(True, alpha=0.3)
            ax.set_xlim(0, 90)
            ax.set_ylim(0, max(max(home_values), max(away_values)) + 0.5)

            plt.tight_layout()

            # 保存为base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            plt.close()

            return image_base64
        except Exception as e:
            print(f"生成xG图表失败: {e}")
            return None

    def generate_shotmap(self, match_id: int, events: pd.DataFrame, team: Optional[str] = None) -> Optional[str]:
        """生成射门地图"""
        try:
            shots = events[events['type'] == 'Shot'].copy()
            if shots.empty:
                return None

            if team:
                shots = shots[shots['team'] == team]

            shots = self.calculate_xg(shots)

            pitch = Pitch(pitch_color='#1a1a2e', line_color='white', line_zorder=2)
            fig, ax = pitch.draw(figsize=(12, 8))

            # 绘制射门点
            for _, shot in shots.iterrows():
                location = shot.get('location')
                if not isinstance(location, (list, tuple)) or len(location) < 2:
                    continue

                x, y = location[0], location[1]
                xg = shot.get('xg', 0.05)

                # 颜色和大小基于xG
                color = '#2ecc71' if shot.get('shot_outcome') == 'Goal' else '#e74c3c'
                size = 200 + xg * 800

                # 标记进球
                marker = 'o'
                if shot.get('shot_outcome') == 'Goal':
                    marker = '*'
                    size *= 1.5

                ax.scatter(x, y, s=size, c=color, marker=marker, alpha=0.7, zorder=3)

            ax.set_title(f'Shot Map - {team or "All Teams"}', fontsize=14, fontweight='bold', color='white')

            plt.tight_layout()
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight', facecolor='#1a1a2e')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            plt.close()

            return image_base64
        except Exception as e:
            print(f"生成射门地图失败: {e}")
            return None

    def generate_heatmap(self, events: pd.DataFrame, team: str) -> Optional[str]:
        """生成热力图"""
        try:
            team_events = events[events['team'] == team].copy()
            if team_events.empty:
                return None

            # 转换坐标
            team_events = self._events_to_vertical_coords(team_events)

            # 提取位置
            locations = team_events['location'].dropna().apply(
                lambda x: [x[0], x[1]] if isinstance(x, (list, tuple)) and len(x) >= 2 else None
            ).dropna().tolist()

            if not locations:
                return None

            locations = np.array(locations)

            pitch = VerticalPitch(pitch_color='#1a1a2e', line_color='white', line_zorder=2)
            fig, ax = pitch.draw(figsize=(12, 8))

            # 绘制热力图
            heatmap = pitch.hexbin(
                locations[:, 0], locations[:, 1],
                ax=ax,
                gridsize=15,
                cmap='YlOrRd',
                alpha=0.7,
                extent=[0, 100, 0, 100]
            )

            ax.set_title(f'Heat Map - {team}', fontsize=14, fontweight='bold', color='white')
            plt.colorbar(heatmap, ax=ax, label='Event Density')

            plt.tight_layout()
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight', facecolor='#1a1a2e')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            plt.close()

            return image_base64
        except Exception as e:
            print(f"生成热力图失败: {e}")
            return None

    def generate_pass_network(self, events: pd.DataFrame, team: str) -> Optional[str]:
        """生成传球网络图"""
        try:
            team_events = events[events['team'] == team].copy()
            passes = team_events[team_events['type'] == 'Pass']

            if passes.empty or len(passes) < 10:
                return None

            # 获取传球位置
            pass_locations = []
            for _, pas in passes.iterrows():
                loc = pas.get('location')
                end_loc = pas.get('pass_end_location')
                if isinstance(loc, (list, tuple)) and isinstance(end_loc, (list, tuple)):
                    pass_locations.append({
                        'from': [loc[0], loc[1]],
                        'to': [end_loc[0], end_loc[1]]
                    })

            if not pass_locations:
                return None

            pitch = Pitch(pitch_color='#1a1a2e', line_color='white', line_zorder=2)
            fig, ax = pitch.draw(figsize=(12, 8))

            # 绘制传球路线
            for p in pass_locations[:30]:  # 限制数量
                ax.annotate(
                    '',
                    xy=(p['to'][0], p['to'][1]),
                    xytext=(p['from'][0], p['from'][1]),
                    arrowprops=dict(arrowstyle='->', color='white', alpha=0.5, lw=1)
                )

            ax.set_title(f'Pass Network - {team}', fontsize=14, fontweight='bold', color='white')

            plt.tight_layout()
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight', facecolor='#1a1a2e')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            plt.close()

            return image_base64
        except Exception as e:
            print(f"生成传球网络失败: {e}")
            return None

    def generate_full_analysis(self, match_id: int, events: pd.DataFrame, home_team: str, away_team: str) -> Dict:
        """生成完整分析图表"""
        return {
            'xg_timeline': self.generate_xg_chart(match_id, events),
            'shotmap_home': self.generate_shotmap(match_id, events, home_team),
            'shotmap_away': self.generate_shotmap(match_id, events, away_team),
            'heatmap_home': self.generate_heatmap(events, home_team),
            'heatmap_away': self.generate_heatmap(events, away_team),
            'pass_network_home': self.generate_pass_network(events, home_team),
            'pass_network_away': self.generate_pass_network(events, away_team)
        }


# 全局可视化服务实例
visualization_service = VisualizationService()


if __name__ == "__main__":
    service = VisualizationService()
    print("可视化服务已初始化")