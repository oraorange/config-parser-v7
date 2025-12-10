import sys
import ply.lex as lex
import ply.yacc as yacc
import yaml

# --- Лексический анализатор ---
tokens = (
    'NUMBER',
    'NAME',
    'LBRACE', 'RBRACE',
    'LPAREN', 'RPAREN',
    'COLON', 'COMMA',
    'SEMICOLON',
    'EQUALS',
    'CONST_USE',
)

t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_COLON = r':'
t_COMMA = r','
t_SEMICOLON = r';'
t_EQUALS = r'='

def t_CONST_USE(t):
    r'§[a-zA-Z_]+§'
    t.value = t.value[1:-1]  # убираем §
    return t

def t_NAME(t):
    r'[a-zA-Z_]+'
    return t

def t_NUMBER(t):
    r'-?(\d+|\d+\.\d*|\.\d+)([eE][-+]?\d+)?'
    t.value = float(t.value) if '.' in t.value or 'e' in t.value.lower() else int(t.value)
    return t

# Многострочные комментарии: --[[ ... ]]
def t_COMMENT(t):
    r'--\[\[[\s\S]*?\]\]'
    t.lexer.lineno += t.value.count('\n')
    pass  # игнорируем

t_ignore = ' \t\n'

def t_error(t):
    print(f"Лексическая ошибка в символе: '{t.value[0]}'", file=sys.stderr)
    t.lexer.skip(1)

lexer = lex.lex()

# --- Синтаксический анализатор ---
constants = {}

def p_config(p):
    '''config : elements'''
    p[0] = p[1]

def p_elements(p):
    '''elements : element elements
                | element'''
    if len(p) == 3:
        if p[1] is not None:
            if isinstance(p[2], dict) and isinstance(p[1], dict):
                p[0] = {**p[1], **p[2]}
            elif p[2] is None:
                p[0] = p[1]
            else:
                p[0] = [p[1]] if not isinstance(p[2], list) else [p[1]] + p[2]
        else:
            p[0] = p[2]
    else:
        p[0] = p[1]

def p_element(p):
    '''element : const_decl
               | dict
               | array'''
    p[0] = p[1]

def p_const_decl(p):
    '''const_decl : NAME EQUALS value SEMICOLON'''
    constants[p[1]] = p[3]
    p[0] = {p[1]: p[3]}

def p_dict(p):
    '''dict : LBRACE pairs RBRACE
            | LBRACE RBRACE'''
    if len(p) == 4:
        p[0] = dict(p[2])
    else:
        p[0] = {}

def p_pairs(p):
    '''pairs : pair
             | pair COMMA pairs'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]

def p_pair(p):
    'pair : NAME COLON value'
    p[0] = (p[1], p[3])

def p_array(p):
    '''array : LPAREN values RPAREN
             | LPAREN RPAREN'''
    if len(p) == 4:
        p[0] = p[2]
    else:
        p[0] = []

def p_values(p):
    '''values : value
              | value COMMA values'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]

def p_value(p):
    '''value : NUMBER
             | dict
             | array
             | CONST_USE'''
    if isinstance(p[1], str):  # CONST_USE
        if p[1] in constants:
            p[0] = constants[p[1]]
        else:
            print(f"Ошибка: константа '{p[1]}' не определена", file=sys.stderr)
            p[0] = None
    else:
        p[0] = p[1]

def p_error(p):
    if p:
        print(f"Синтаксическая ошибка в токене: {p.type} ('{p.value}') на строке {p.lineno}", file=sys.stderr)
    else:
        print("Синтаксическая ошибка: неожиданный конец файла", file=sys.stderr)

parser = yacc.yacc()

# --- Преобразование в YAML ---
def to_yaml(data):
    if data is None:
        return ""
    return yaml.dump(data, allow_unicode=True, default_flow_style=False)

# --- Главная функция ---
def main():
    input_text = sys.stdin.read()
    
    if not input_text.strip():
        print("Входные данные пусты", file=sys.stderr)
        sys.exit(1)
    
    result = parser.parse(input_text, lexer=lexer, debug=False)
    
    if result is not None:
        yaml_output = to_yaml(result)
        print(yaml_output)
    else:
        print("Ошибка разбора", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
