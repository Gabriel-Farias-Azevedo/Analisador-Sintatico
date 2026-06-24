import ply.lex as lex

# Mapeamento de palavras reservadas da linguagem
reserved = {
    'dispositivo': 'DISPOSITIVO',
    'set': 'SET',
    'se': 'SE',
    'entao': 'ENTAO',
    'senao': 'SENAO',
    'enviar': 'ENVIAR',
    'alerta': 'ALERTA',
    'para': 'PARA',
    'todos': 'TODOS',
    'ligar': 'LIGAR',
    'desligar': 'DESLIGAR',
    'verificar': 'VERIFICAR',
    'True': 'BOOL',
    'False': 'BOOL',
    "fim": 'FIM'
}

# Lista de todos os tokens reconhecidos pelo analisador
tokens = [
    'NUM',
    'NAMEDEVICE',
    'MSG',
    'OPLOGIC',
    'AND',
    'PONTO',
    'DOIS_PONTOS',
    'VIRGULA',
    'ABRE_CHAVE',
    'FECHA_CHAVE',
    'ABRE_PARENTESE',
    'FECHA_PARENTESE',
    'IGUAL'
] + list(set(reserved.values()))

# Definição dos tokens simples via expressões regulares
t_AND = r'&&'
t_PONTO = r'\.'
t_DOIS_PONTOS = r':'
t_VIRGULA = r','
t_ABRE_CHAVE = r'\{'
t_FECHA_CHAVE = r'\}'
t_ABRE_PARENTESE = r'\('
t_FECHA_PARENTESE = r'\)'
t_IGUAL = r'='

# Reconhece operadores lógicos de comparação
def t_OPLOGIC(t):
    r'==|!=|>=|<=|>|<'
    return t

# Reconhece e processa strings removendo as aspas
def t_MSG(t):
    r'"[^"\n]*"'
    t.value = t.value.strip('"') 
    return t

# Reconhece números inteiros e converte para tipo int
def t_NUM(t):
    r'\d+'
    t.value = int(t.value)
    return t

# Reconhece identificadores e verifica se são palavras reservadas
def t_NAMEDEVICE(t):
    r'[a-zA-Z]+'
    if t.value in reserved:
        t.type = reserved[t.value]
        if t.type == 'BOOL':
            t.value = True if t.value == 'True' else False
    else:
        t.type = 'NAMEDEVICE'
    return t

# Define caracteres ignorados (espaços e tabs)
t_ignore = ' \t'

# Atualiza o contador de linhas ao encontrar quebras de linha
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Reporta erros de caracteres não reconhecidos
def t_error(t):
    print(f"Erro léxico: Caractere inválido '{t.value[0]}' na linha {t.lineno}")
    t.lexer.skip(1)

# Inicializa o motor do analisador léxico
lexer = lex.lex()