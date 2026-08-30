from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'app.js').read_text(encoding='utf-8')
assert 'exerciseRecallExerciseId' in s
assert 'exerciseRecallLoading' in s
assert 'exerciseProgressionExerciseId' in s
assert 'if(S.exerciseRecallExerciseId===exerciseId)' in s
assert 'exerciseRecallMarkup(e)' in s
assert 'S.exerciseRecall=null;S.exerciseRecallExerciseId=null' in s
assert (ROOT/'VERSION.txt').read_text().strip() in {'14.74.1','14.74.3'}
print('v14.74.1 exercise history reload regression: passed')
