import ply.yacc as yacc
from lexer import tokens
import os
import glob

# Tabelas para armazenar dispositivos e seus sensores
dispositivos_declarados = {}
sensores_declarados = set()
sensores_inicializados = set()

# Lista que armazena o código gerado em Python
codigo_python = ["from runtime import *", ""]

# Aplica indentação em blocos de código gerados
def indentar(linhas, espacos=4):
    recuo = " " * espacos
    return [recuo + line for line in linhas]

# Define a precedência para evitar ambiguidade em comandos condicionais
precedence = (
    ('nonassoc', 'ENTAO'),
    ('nonassoc', 'SENAO'),
)

# Regra principal que consolida o programa e inicializa sensores vazios
def p_programa_raiz(p):
    'program : devices cmds'
    for sensor in sensores_declarados:
        if sensor not in sensores_inicializados:
            codigo_python.insert(len(dispositivos_declarados) + 2, f"{sensor} = 0")
    codigo_python.extend(p[2])
    p[0] = "Sucesso"

# Processa declarações de dispositivos
def p_lista_dispositivos(p):
    '''devices : device devices
               | device'''
    pass

# Registra um dispositivo sem sensor
def p_declaracao_dispositivo_simples(p):
    'device : DISPOSITIVO DOIS_PONTOS ABRE_CHAVE NAMEDEVICE FECHA_CHAVE'
    dispositivos_declarados[p[4]] = None

# Registra um dispositivo com sensor vinculado
def p_declaracao_dispositivo_com_sensor(p):
    'device : DISPOSITIVO DOIS_PONTOS ABRE_CHAVE NAMEDEVICE VIRGULA NAMEDEVICE FECHA_CHAVE'
    dispositivos_declarados[p[4]] = p[6]
    sensores_declarados.add(p[6])

# Agrupa a lista de comandos do programa
def p_bloco_comandos(p):
    '''cmds : cmd cmds
            | cmd'''
    if len(p) == 3:
        p[0] = p[1] + p[2]
    else:
        p[0] = p[1]

# Identifica o tipo de comando (atribuição, ação ou condição)
def p_reducao_comando_individual(p):
    '''cmd : attrib PONTO
           | act PONTO
           | obsact'''
    p[0] = p[1]

# Realiza atribuição de valor fixo a um sensor
def p_atribuicao_valor_estatico(p):
    'attrib : SET NAMEDEVICE IGUAL var'
    sensor = p[2]
    sensores_inicializados.add(sensor)
    p[0] = [f"{sensor} = {p[4]}"]

# Realiza atribuição de leitura de sensor
def p_atribuicao_leitura_sensor(p):
    'attrib : SET NAMEDEVICE IGUAL expressao_leitura'
    sensor = p[2]
    sensores_inicializados.add(sensor)
    p[0] = [f"{sensor} = {p[4]}"]

# Retorna o valor de uma variável (número ou booleano)
def p_tipo_variavel(p):
    '''var : NUM
           | BOOL'''
    p[0] = p[1]

# Processa estrutura condicional simples
def p_condicional_if(p):
    'obsact : SE obs ENTAO cmds'
    linhas_corpo = indentar(p[4])
    p[0] = [f"if {p[2]}:"] + linhas_corpo

# Processa estrutura condicional com senao
def p_condicional_if_else(p):
    'obsact : SE obs ENTAO cmds SENAO cmds'
    linhas_if = indentar(p[4])
    linhas_else = indentar(p[6])
    p[0] = [f"if {p[2]}:"] + linhas_if + ["else:"] + linhas_else

# Processa expressão lógica composta com AND
def p_expressao_logica_composta(p):
    'obs : obs AND condicao_simples'
    p[0] = f"{p[1]} and {p[3]}"

# Processa expressão lógica simples
def p_expressao_logica_simples(p):
    'obs : condicao_simples'
    p[0] = p[1]

# Processa a comparação entre sensor e valor
def p_predicado_relacional(p):
    'condicao_simples : NAMEDEVICE OPLOGIC var'
    op = '==' if p[2] == '=' else p[2]
    p[0] = f"{p[1]} {op} {p[3]}"

# Direciona para o tipo de ação de hardware
def p_reducao_acao_dispositivo(p):
    '''act : actexecute
           | actalert'''
    p[0] = p[1]

# Processa comandos de ação simples
def p_comando_execucao_isolada(p):
    'actexecute : expressao_leitura'
    p[0] = [p[1]]

# Gera a chamada da função de hardware
def p_chamada_funcao_atuador(p):
    'expressao_leitura : action NAMEDEVICE'
    p[0] = f'{p[1]}("{p[2]}")'

# Mapeia a ação do comando para a função correspondente
def p_mapeamento_token_acao(p):
    '''action : LIGAR
              | DESLIGAR
              | VERIFICAR'''
    p[0] = p[1]

# Processa envio de alertas para um ou mais alvos
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

# Processa mensagem de alerta simples
def p_mensagem_literal(p):
    'msg_formatada : MSG'
    p[0] = (p[1], None)

# Processa mensagem de alerta com variável
def p_mensagem_interpolada(p):
    'msg_formatada : MSG VIRGULA NAMEDEVICE'
    p[0] = (p[1], p[3])

# Processa envio para todos os dispositivos
def p_alvos_broadcast_total(p):
    'alvos : TODOS'
    p[0] = list(dispositivos_declarados.keys())

# Processa lista recursiva de dispositivos alvo
def p_alvos_lista_recursiva(p):
    'alvos : NAMEDEVICE VIRGULA alvos'
    p[0] = [p[1]] + p[3]

# Processa alvo único
def p_alvos_unitario(p):
    'alvos : NAMEDEVICE'
    p[0] = [p[1]]

# Rotina de tratamento de erros sintáticos
def p_error(p):
    if p:
        print(f"Erro sintático na linha {p.lineno}: '{p.value}'")
    else:
        print("Erro sintático: fim inesperado do arquivo")

# Inicializa o parser
parser = yacc.yacc(method='LALR')

# Bloco principal para processar os arquivos de teste
if __name__ == "__main__":
    arquivos = sorted(glob.glob(os.path.join("tests", "*.txt")))
    
    for caminho in arquivos:
        nome_puro = os.path.splitext(os.path.basename(caminho))[0]
        arquivo_saida = f"output_{nome_puro}.py"
        
        # Limpa variáveis para o próximo arquivo
        dispositivos_declarados.clear()
        sensores_declarados.clear()
        sensores_inicializados.clear()
        codigo_python = ["from runtime import *", ""]
        
        with open(caminho, "r") as f:
            parser.parse(f.read())
            
        with open(arquivo_saida, "w") as f:
            f.write("\n".join(codigo_python))
        print(f"Processado: {nome_puro} -> {arquivo_saida}")