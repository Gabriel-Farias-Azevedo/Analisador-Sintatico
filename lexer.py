# lexer.py
import ply.lex as lex

# --- DICIONÁRIO DE PALAVRAS RESERVADAS (KEYWORDS) ---
# Mapeamento estático de lexemas que possuem significado semântico fixo na GLC.
# Impede que palavras-chave sejam erroneamente classificadas como identificadores comuns.
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
    'False': 'BOOL'
}

# --- LISTA GLOBAL DE TOKENS (ALFABETO DO PARSER) ---
# Define o conjunto de terminais válidos que o analisador léxico extrairá do fluxo de caracteres
# e enviará para o analisador sintático ascendente LALR(1).
tokens = [
    'NUM',
    'NAMEDEVICE',
    'OBSERVATION',
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

# --- EXPRESSÕES REGULARES PARA TOKENS TERMINAIS SIMPLES ---
# Definição de padrões imutáveis por meio de Expressões Regulares (RegEx).
t_AND = r'&&'
t_PONTO = r'\.'
t_DOIS_PONTOS = r':'
t_VIRGULA = r','
t_ABRE_CHAVE = r'\{'
t_FECHA_CHAVE = r'\}'
t_ABRE_PARENTESE = r'\('
t_FECHA_PARENTESE = r'\)'
t_IGUAL = r'='

# --- FUNÇÕES DE RECONHECIMENTO DE TOKENS COMPLEXOS ---

def t_OPLOGIC(t):
    r'==|!=|>=|<=|>|<'
    """
    Subrotina Léxica: Operadores Relacionais.
    Captura operadores booleanos de comparação respeitando a ordem de 
    precedência de casamento de padrões (maiores operadores primeiro, como '>=' antes de '>').
    """
    return t

def t_MSG(t):
    r'"[^"\n]*"'
    """
    Subrotina Léxica: Literais de Cadeias de Caracteres (String Literals).
    Reconhece o lexema delimitado por aspas duplas, realizando o tratamento semântico
    prévio de extração das aspas para facilitar o consumo nas rotinas de alerta do parser.
    """
    t.value = t.value.strip('"') 
    return t

def t_NUM(t):
    r'\d+'
    """
    Subrotina Léxica: Literais Numéricos Inteiros.
    Identifica sequências de dígitos decimais e realiza a coerção de tipo (Casting)
    da string capturada para o tipo primitivo 'int' do Python para fins de avaliação semântica.
    """
    t.value = int(t.value)
    return t

def t_NAMEDEVICE(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    """
    Subrotina Léxica: Identificadores Gerais e Palavras Reservadas.
    Aplica o padrão clássico de identificadores. Realiza uma busca retroativa na tabela de 
    palavras reservadas (`reserved`) para desviar e reclassificar o token caso corresponda 
    a uma keyword da linguagem ou a um literal booleano (True/False).
    """
    if t.value in reserved:
        t.type = reserved[t.value]
        if t.type == 'BOOL':
            t.value = True if t.value == 'True' else False
    else:
        # Mantém como NAMEDEVICE. A especificação contextual entre dispositivo e sensor
        # é postergada para tratamento e validação durante a análise sintática.
        t.type = 'NAMEDEVICE'
    return t

# --- CANAIS DE IGNORÊNCIA E DIRETIVAS DO COMPILADOR ---

# t_ignore: Define os caracteres de descarte (espaço em branco e tabulação)
# que não geram tokens e servem apenas como delimitadores léxicos.
t_ignore = ' \t'

def t_newline(t):
    r'\n+'
    """
    Subrotina de Controle de Contexto Espacial:
    Incrementa dinamicamente o contador global de linhas do Lexer ao encontrar
    quebras de linha, garantindo o rastreamento preciso para relatórios de erro sintático/léxico.
    """
    t.lexer.lineno += len(t.value)

def t_error(t):
    """
    Rotina de Tratamento de Exceções Léxicas:
    Invocada quando o ponteiro de leitura do autômato não consegue transicionar para 
    nenhum estado de aceitação baseado nos padrões de tokens definidos.
    """
    print(f"Erro léxico: Caractere inválido '{t.value[0]}' na linha {t.lineno}")
    t.lexer.skip(1)

# Inicialização do Engine do Mapeador Léxico através do PLY
lexer = lex.lex()