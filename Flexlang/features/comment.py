from engine import syntax

@syntax(r'#.*')
def comment(match, runtime):
    pass