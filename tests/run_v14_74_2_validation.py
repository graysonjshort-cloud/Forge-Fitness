from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'app.js').read_text(encoding='utf-8')
checks=[
  'swapOptionsKey', 'swapOptionsLoading', 'swapOptionsLoaded',
  'substitutionIntelligenceExerciseId', 'substitutionIntelligenceLoading',
  'cardioSwapKey', 'cardioSwapLoaded',
  'progressHubLoading', 'strengthTrendLoading', 'coachLoading', 'coachBriefingLoading',
  'recoveryIntelligenceLoading', 'adaptationPreviewLoading',
  'historyRowsMarkup()', 'exerciseHistoryMarkup()', 'swapOptionsMarkup(e)', 'cardioSwapMarkup()'
]
for x in checks: assert x in s, f'missing async-stability guard: {x}'
assert 'if(S.swapOptionsKey===key&&(S.swapOptionsLoaded||S.swapOptionsLoading))return;' in s
assert 'if(S.substitutionIntelligenceExerciseId===exerciseId&&(S.substitutionIntelligence||S.substitutionIntelligenceLoading))return;' in s
assert 'if(S.exerciseProgressionLoading)return' not in s, 'new exercise can be blocked by stale progression request'
assert (ROOT/'VERSION.txt').read_text().strip()=='14.74.2'
print('v14.74.2 async loader stability regression: passed')
