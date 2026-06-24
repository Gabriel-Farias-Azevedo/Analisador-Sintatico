import ply.yacc as yacc
from lexer import tokens
import os
import glob

dispositivos_declarados = {}
sensores_declarados = set()
sensores_inicializados = set()
codigo_python = ["from runtime import *", ""]

def indentar(linhas, espacos=4):
    recuo = " " * espacos
    if isinstance(linhas, str):
        linhas = [linhas]
    return [recuo + line for line in linhas]

precedence = (
    ('nonassoc', 'ENTAO'),
    ('nonassoc', 'SENAO'),
)

# Define a regra principal do programa e finaliza a injeção de código
def p_programa_raiz(p):
    'program : devices cmds'
    for sensor in sensores_declarados:
        if sensor not in sensores_inicializados:
            codigo_python.insert(len(dispositivos_declarados) + 2, f"{sensor} = 0")
    codigo_python.extend(p[2])
    p[0] = "Sucesso"

# Regra recursiva para capturar múltiplos dispositivos
def p_lista_dispositivos(p):
    '''devices : device devices
               | device'''
    pass

# Registra um dispositivo sem sensor associado
def p_declaracao_dispositivo_simples(p):
    'device : DISPOSITIVO DOIS_PONTOS ABRE_CHAVE NAMEDEVICE FECHA_CHAVE'
    dispositivos_declarados[p[4]] = None

# Registra um dispositivo associado a um sensor
def p_declaracao_dispositivo_com_sensor(p):
    'device : DISPOSITIVO DOIS_PONTOS ABRE_CHAVE NAMEDEVICE VIRGULA NAMEDEVICE FECHA_CHAVE'
    dispositivos_declarados[p[4]] = p[6]
    sensores_declarados.add(p[6])

# Regra para tratar lista de comandos sem causar conflitos de shift/reduce
def p_bloco_comandos(p):
    '''cmds : comando cmds
            | comando'''
    if len(p) == 3:
        p[0] = p[1] + p[2]
    else:
        p[0] = p[1]

# Unifica o que é um comando executável vs estruturas de controle
def p_comando(p):
    '''comando : attrib PONTO
               | act PONTO
               | obsact'''
    p[0] = p[1]
    
# Transpila atribuição de valores fixos (números ou booleanos)
def p_atribuicao_valor_estatico(p):
    'attrib : SET NAMEDEVICE IGUAL var'
    sensores_inicializados.add(p[2])
    p[0] = [f"{p[2]} = {p[4]}"]

# Transpila atribuição baseada em leitura de sensor
def p_atribuicao_leitura_sensor(p):
    'attrib : SET NAMEDEVICE IGUAL expressao_leitura'
    sensores_inicializados.add(p[2])
    p[0] = [f"{p[2]} = {p[4]}"]

# Identifica tipos de dados literais permitidos
def p_tipo_variavel(p):
    '''var : NUM
           | BOOL'''
    p[0] = p[1]

# Transpila estrutura condicional SE simples
def p_condicional_if(p):
    'obsact : SE obs ENTAO cmds FIM'
    p[0] = [f"if {p[2]}:"] + indentar(p[4])

# Transpila estrutura condicional SE/SENAO
def p_condicional_if_else(p):
    'obsact : SE obs ENTAO cmds SENAO cmds FIM'
    p[0] = [f"if {p[2]}:"] + indentar(p[4]) + ["else:"] + indentar(p[6])

# Processa operações lógicas AND
def p_expressao_logica_composta(p):
    'obs : obs AND condicao_simples'
    p[0] = f"{p[1]} and {p[3]}"

# Regra base para expressões lógicas
def p_expressao_logica_simples(p):
    'obs : condicao_simples'
    p[0] = p[1]

# Converte predicados relacionais ObsAct para Python
def p_predicado_relacional(p):
    'condicao_simples : NAMEDEVICE OPLOGIC var'
    op = '==' if p[2] == '=' else p[2]
    p[0] = f"{p[1]} {op} {p[3]}"

# Agrupa ações de execução e alertas
def p_reducao_acao_dispositivo(p):
    '''act : actexecute
           | actalert'''
    p[0] = p[1]

# Encapsula comandos de atuadores
def p_comando_execucao_isolada(p):
    'actexecute : expressao_leitura'
    p[0] = [p[1]]

# Transpila chamada de funções do runtime
def p_chamada_funcao_atuador(p):
    'expressao_leitura : action NAMEDEVICE'
    p[0] = f'{p[1]}("{p[2]}")'

# Mapeia tokens de ação para nomes de funções do runtime
def p_mapeamento_token_acao(p):
    '''action : LIGAR
              | DESLIGAR
              | VERIFICAR'''
    p[0] = p[1]

# Transpila o envio de alertas
def p_comando_envio_alerta(p):
    'actalert : ENVIAR ALERTA ABRE_PARENTESE msg_formatada FECHA_PARENTESE PARA alvos'
    linhas = []
    mensagem, variavel = p[4]
    for dispositivo in p[7]:
        if variavel:
            linhas.append(f'alerta("{dispositivo}", "{mensagem}", {variavel})')
        else:
            linhas.append(f'alerta("{dispositivo}", "{mensagem}")')
    p[0] = linhas

# Define mensagem sem variáveis
def p_mensagem_literal(p):
    'msg_formatada : MSG'
    p[0] = (p[1], None)

# Define mensagem com variável interpolada
def p_mensagem_interpolada(p):
    'msg_formatada : MSG VIRGULA NAMEDEVICE'
    p[0] = (p[1], p[3])

# Captura o envio de alerta para todos os dispositivos
def p_alvos_broadcast_total(p):
    'alvos : TODOS DOIS_PONTOS'
    p[0] = list(dispositivos_declarados.keys())

# Regra para processar lista de dispositivos específicos
def p_alvos_lista_recursiva(p):
    'alvos : NAMEDEVICE VIRGULA alvos'
    p[0] = [p[1]] + p[3]

# Regra para um único alvo na lista
def p_alvos_unitario(p):
    'alvos : NAMEDEVICE'
    p[0] = [p[1]]

# Tratamento de erros sintáticos
def p_error(p):
    if p:
        print(f"Erro sintático na linha {p.lineno}: token inesperado '{p.value}'")
    else:
        print("Erro sintático: fim inesperado do arquivo")

parser = yacc.yacc(method='LALR')

if __name__ == "__main__":
    for caminho in glob.glob(os.path.join("tests", "*.txt")):
        nome_puro = os.path.splitext(os.path.basename(caminho))[0]
        dispositivos_declarados.clear()
        sensores_declarados.clear()
        sensores_inicializados.clear()
        codigo_python = ["from runtime import *", ""]
        with open(caminho, "r") as f:
            parser.parse(f.read())
        with open(f"output_{nome_puro}.py", "w") as f:
            f.write("\n".join(codigo_python))
        print(f"Processado: {nome_puro}")