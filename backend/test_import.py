"""调试脚本：测试各模块导入"""
import sys, time
sys.path.insert(0, r'C:\Users\ASUS\football-ai\backend')

print('1: importing pandas...')
import pandas as pd
print('2: pandas OK')

print('3: importing pathlib...')
from pathlib import Path
print('4: pathlib OK')

print('5: importing data_service...')
from services.data_service import DataService
print('6: data_service imported')

ds = DataService()
print('7: DataService created')
matches = ds.get_matches()
print(f'8: matches loaded: {len(matches)}')

print('9: importing prediction_service...')
from services.prediction_service import PredictionService
print('10: prediction_service imported')
ps = PredictionService()
print(f'11: model loaded: {ps.model is not None}, ELO teams: {len(ps.elo_ratings)}')

result = ps.predict('Argentina', 'Brazil')
print(f'12: prediction: {result}')
print('DONE!')
