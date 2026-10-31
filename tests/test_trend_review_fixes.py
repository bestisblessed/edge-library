import importlib
import sys
from unittest.mock import patch

import pytest

NAMES = ['lions_extra_rest_after_scoring', 'eagles_home_underdog',
         'eagles_division_underdog', 'cowboys_after_big_under']

@pytest.mark.parametrize('name', NAMES)
def test_notebook_summary_matches_qualifiers(name):
    m = importlib.import_module('scripts.' + name)
    result = m.analyze(m.load_games(minimum_season=2010, require_scores=False))
    shown = []
    with patch('IPython.display.display', side_effect=shown.append):
        m.show_notebook_tables(result)
    table = shown[1].data.iloc[0]
    qualifiers = result.audit[result.audit.qualifies]
    if name.startswith('lions'):
        assert table['wins'] == result.metadata['claimed_overs'] == 14
        assert table['games'] == qualifiers.total_result.notna().sum()
    else:
        assert table['su_wins'] == result.metadata['claimed_su_wins']
        assert table['ats_wins'] == result.metadata['claimed_ats_wins']
        assert table['games'] == qualifiers.su_result.notna().sum()

@pytest.mark.parametrize('name,expected', [('eagles_home_underdog',13), ('cowboys_after_big_under',14)])
def test_cli_season_and_date_windows(name, expected):
    m = importlib.import_module('scripts.' + name)
    games = m.load_games(minimum_season=2010, require_scores=False)
    for argv, date in [([], m.DEFAULT_START_DATE), (['--start-season','2020'], None),
                       (['--start-season','2020','--start-date','2021-01-01'], '2021-01-01')]:
        real_analyze = m.analyze
        with patch.object(sys, 'argv', [name] + argv), \
             patch.object(m, 'analyze', wraps=real_analyze) as analyze, \
             patch.object(m, 'print_report'), patch.object(m, 'show_charts'):
            assert m.main() == 0
        assert analyze.call_args.kwargs['start_date'] == date
        if argv == ['--start-season','2020']:
            result = real_analyze(games, start_season=2020, start_date=date)
            assert len(result.audit[result.audit.qualifies]) == expected
