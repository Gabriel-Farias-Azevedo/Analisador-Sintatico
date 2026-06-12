# parser.py
import ply.yacc as yacc
from lexer import tokens

# tabelas de Símbolos e Estruturas de Dados do Compilador
# dispositivos_declarados: Mapeia o identificador do dispositivo ao seu respectivo sensor (se houver)
dispositivos_declarados = {}
# sensores_declarados: Conjunto de variáveis/sensores identificados na definição dos dispositivos
sensores_declarados = set()
# sensores_inicializados: Monitora quais sensores receberam carga inicial via comando 'set'
sensores_inicializados = set()

# Código Objeto (Intermediate/Target Representation) gerado em Python
codigo_python = ["from runtime import *", ""]

def indentar(linhas, espacos=4):
    """
    Subrotina Semântica Auxiliar:
    Aplica indentação em blocos de escopo aninhados (geração de blocos em Python).
    """
    recuo = " " * espacos
    return [recuo + line for line in linhas]

# --- DEFINIÇÃO DE PRECEDÊNCIA SINTÁTICA ---
# Resolução do problema clássico de ambiguidade "Dangling Else" (Senão Pendente)
# Define que o token SENAO possui maior precedência que ENTAO para forçar o Shift
precedence = (
    ('nonassoc', 'ENTAO'),
    ('nonassoc', 'SENAO'),
)

# --- REGRAS DE PRODUÇÃO DA GRAMÁTICA (ANÁLISE SINTÁTICA) ---

def p_programa_raiz(p):
    'program : devices cmds'
    """
    Regra Raiz (Símbolo Inicial):
    Responsável por consolidar a árvore de sintaxe abstrata. Realiza a checagem 
    estática de sensores declarados mas não inicializados (regra de suposição 1.4),
    injetando o valor default (0) antes de estender o código global com os comandos.
    """
    for sensor in sensores_declarados:
        if sensor not in sensores_inicializados:
            codigo_python.insert(len(dispositivos_declarados) + 2, f"{sensor} = 0")
    
    codigo_python.extend(p[2])
    p[0] = "Transpilação sintática concluída com sucesso!"

def p_lista_dispositivos(p):
    '''devices : device devices
               | device'''
    """
    Produção de Recursão à Esquerda/Direita:
    Processa a subárvore de mapeamento e declaração da infraestrutura de hardware.
    """
    pass

def p_declaracao_dispositivo_simples(p):
    'device : DISPOSITIVO DOIS_PONTOS ABRE_CHAVE NAMEDEVICE FECHA_CHAVE'
    """
    Ação Semântica: Declaração de Dispositivo Atuador Simples.
    Popula a Tabela de Símbolos registrando o ID do dispositivo sem sensores vinculados.
    """
    dispositivos_declarados[p[4]] = None

def p_declaracao_dispositivo_com_sensor(p):
    'device : DISPOSITIVO DOIS_PONTOS ABRE_CHAVE NAMEDEVICE VIRGULA NAMEDEVICE FECHA_CHAVE'
    """
    Ação Semântica: Declaração de Dispositivo Complexo (Atuador + Sensor/Observação).
    Registra o vínculo entre o dispositivo e sua respectiva variável de monitoramento.
    """
    dispositivos_declarados[p[4]] = p[6]
    sensores_declarados.add(p[6])

def p_bloco_comandos(p):
    '''cmds : cmd cmds
            | cmd'''
    """
    Produção de Bloco de Controle (Instruções Sequenciais):
    Sintetiza e propaga uma lista plana contendo as linhas de código intermediárias,
    garantindo que múltiplos comandos em uma mesma ramificação mantenham a ordenação.
    """
    if len(p) == 3:
        p[0] = p[1] + p[2]
    else:
        p[0] = p[1]

def p_reducao_comando_individual(p):
    '''cmd : attrib PONTO
           | act PONTO
           | obsact'''
    """
    Regra de Derivação Alternativa de Comando (cmd):
    Encaminha os nós de atribuição, ações isoladas (terminadas em ponto) 
    ou blocos de fluxo condicional estruturado para cima na árvore sintática.
    """
    p[0] = p[1]

def p_atribuicao_valor_estatico(p):
    'attrib : SET NAMEDEVICE IGUAL var'
    """
    Síntese Semântica: Atribuição Direta (Literal/Booleano).
    Valida a inicialização da variável na tabela e traduz para a sintaxe Python.
    """
    sensor = p[2]
    sensores_inicializados.add(sensor)
    p[0] = [f"{sensor} = {p[4]}"]

def p_atribuicao_leitura_sensor(p):
    'attrib : SET NAMEDEVICE IGUAL expressao_leitura'
    """
    Síntese Semântica: Atribuição por Chamada de Função de Hardware (I/O).
    Associa o retorno dinâmico de uma ação de verificação ao identificador do sensor.
    """
    sensor = p[2]
    sensores_inicializados.add(sensor)
    p[0] = [f"{sensor} = {p[4]}"]

def p_tipo_variavel(p):
    '''var : NUM
           | BOOL'''
    """
    Regra de Tipagem Léxica:
    Retorna o valor do terminal (Numérico ou Booleano) como string pura para concatenação.
    """
    p[0] = p[1]

def p_condicional_if(p):
    'obsact : SE obs ENTAO cmds'
    """
    Síntese Semântica: Estrutura de Controle Unidirecional (if).
    Cria uma ramificação condicional básica aplicando a indentação no bloco interno de comandos.
    """
    linhas_corpo = indentar(p[4])
    p[0] = [f"if {p[2]}:"] + linhas_corpo

def p_condicional_if_else(p):
    'obsact : SE obs ENTAO cmds SENAO cmds'
    """
    Síntese Semântica: Estrutura de Controle Bidirecional (if/else).
    Trata ambas as ramificações de desvio de fluxo e formata o escopo de cada bloco isoladamente.
    """
    linhas_if = indentar(p[4])
    linhas_else = indentar(p[6])
    p[0] = [f"if {p[2]}:"] + linhas_if + ["else:"] + linhas_else

def p_expressao_logica_composta(p):
    'obs : obs AND condicao_simples'
    """
    Produção de Expressão Booleana Composta:
    Avalia predicados encadeados pelo operador de conjunção lógica '&&' (mapeado para 'and').
    """
    p[0] = f"{p[1]} and {p[3]}"

def p_expressao_logica_simples(p):
    'obs : condicao_simples'
    """
    Produção de Expressão Booleana Unitária:
    Propaga a avaliação de um único predicado relacional.
    """
    p[0] = p[1]

def p_predicado_relacional(p):
    'condicao_simples : NAMEDEVICE OPLOGIC var'
    """
    Síntese Semântica: Tradução de Operador Relacional.
    Normaliza operadores particulares da linguagem (como '=' para comparação '==') no Python.
    """
    op = '==' if p[2] == '=' else p[2]
    p[0] = f"{p[1]} {op} {p[3]}"

def p_reducao_acao_dispositivo(p):
    '''act : actexecute
           | actalert'''
    """
    Regra de Derivação de Ações:
    Encaminha comandos operacionais de acionamento ou sinalização externa.
    """
    p[0] = p[1]

def p_comando_execucao_isolada(p):
    'actexecute : expressao_leitura'
    """
    Síntese Semântica: Comando de Ação Executável Isolado.
    Encapsula o comando textual de acionamento puro de hardware em uma estrutura de lista.
    """
    p[0] = [p[1]]

def p_chamada_funcao_atuador(p):
    'expressao_leitura : action NAMEDEVICE'
    """
    Síntese Semântica: Expressão de Chamada Operacional.
    Gera a string de chamada sintática de função para a API do runtime (ex: ligar("Device")).
    """
    p[0] = f'{p[1]}("{p[2]}")'

def p_mapeamento_token_acao(p):
    '''action : LIGAR
              | DESLIGAR
              | VERIFICAR'''
    """
    Mapeamento de Palavras Reservadas Operacionais:
    Propaga o lexema textual da ação direta identificada pelo analisador léxico.
    """
    p[0] = p[1]

def p_comando_envio_alerta(p):
    'actalert : ENVIAR ALERTA ABRE_PARENTESE msg_formatada FECHA_PARENTESE PARA alvos'
    """
    Síntese Semântica: Geração de Eventos e Multi-Alvos (Broadcast).
    Itera recursivamente sobre a lista coletada de alvos para desmembrar o comando 
    original do ObsAct em N chamadas explícitas individuais no código em Python.
    """
    linhas = []
    mensagem, variavel = p[4]
    
    for dispositivo in p[7]:
        if variavel:
            linhas.append(f'alerta("{dispositivo}", "{mensagem}", {variavel})')
        else:
            linhas.append(f'alerta("{dispositivo}", "{mensagem}")')
    p[0] = linhas

def p_mensagem_literal(p):
    'msg_formatada : MSG'
    """
    Tratamento de Argumentos de Mensagem: Tipo Estático.
    Retorna uma tupla contendo o corpo da mensagem limpo de variáveis associadas.
    """
    p[0] = (p[1], None)

def p_mensagem_interpolada(p):
    'msg_formatada : MSG VIRGULA NAMEDEVICE'
    """
    Tratamento de Argumentos de Mensagem: Tipo Dinâmico (Interpolação de Estado).
    Retorna uma tupla associando a mensagem fixa ao registrador do sensor correspondente.
    """
    p[0] = (p[1], p[3])

def p_alvos_broadcast_total(p):
    'alvos : TODOS'
    """
    Tratamento de Alvos: Enumeração Global.
    Acessa a tabela de símbolos de dispositivos coletados para retornar a lista de chaves.
    """
    p[0] = list(dispositivos_declarados.keys())

def p_alvos_lista_recursiva(p):
    'alvos : NAMEDEVICE VIRGULA alvos'
    """
    Tratamento de Alvos: Lista Linear Definida.
    Concatena o identificador atual de dispositivo de forma recursiva aos demais alvos.
    """
    p[0] = [p[1]] + p[3]

def p_alvos_unitario(p):
    'alvos : NAMEDEVICE'
    """
    Tratamento de Alvos: Instância Unitária.
    Inicializa a lista base contendo o único identificador mapeado.
    """
    p[0] = [p[1]]

def p_error(p):
    """
    Rotina de Tratamento de Exceções Sintáticas:
    Disparada pelo motor do Yacc quando nenhum mapeamento de redução LALR(1) é válido.
    """
    if p:
        print(f"Erro sintático próximo ao token '{p.value}' na linha {p.lineno}")
    else:
        print("Erro sintático: Fim de arquivo inesperado")

# Inicialização do Engine do Parser LALR(1) através do PLY
parser = yacc.yacc(method='LALR')


if __name__ == "__main__":
    import os
    import glob

    diretorio_testes = "tests"
    padrao_busca = os.path.join(diretorio_testes, "*.txt")
    
    # Coleta e ordena todos os arquivos .txt dentro da pasta 'testes'
    arquivos_testes = sorted(glob.glob(padrao_busca))

    if not arquivos_testes:
        print(f"[-] Erro: Nenhum arquivo '.txt' encontrado na pasta '{diretorio_testes}'.")
        print("[*] Certifique-se de criar a pasta 'tests' no mesmo diretorio e colocar os arquivos nela.")
    else:
        print(f"[+] Iniciando lote de transpilacao automatica ({len(arquivos_testes)} arquivos encontrados)\n")
        print("=" * 60)

        # Laço para iterar sobre cada caso de teste encontrado
        for caminho_arquivo in arquivos_testes:
            nome_arquivo = os.path.basename(caminho_arquivo)
            nome_puro = os.path.splitext(nome_arquivo)[0]
            arquivo_saida = f"output_{nome_puro}.py"

            print(f"[PROCESSANDO] {nome_arquivo} -> {arquivo_saida}")

            # --- REINICIALIZAÇÃO DO ESTADO SEMÂNTICO ---
            # Limpa as estruturas para que as declarações de um teste não vazem para o próximo
            dispositivos_declarados.clear()
            sensores_declarados.clear()
            sensores_inicializados.clear()
            codigo_python = ["from runtime import *", ""]

            try:
                # Carrega o código fonte em ObsAct
                with open(caminho_arquivo, "r", encoding="utf-8") as f_in:
                    codigo_fonte = f_in.read()

                # Executa a análise e preenche a lista 'codigo_python'
                parser.parse(codigo_fonte)

                # Grava o arquivo de saída correspondente
                with open(arquivo_saida, "w", encoding="utf-8") as f_out:
                    f_out.write("\n".join(codigo_python))
                
                print(f"  -> OK: Transpilação concluída com sucesso.")

            except Exception as e:
                print(f"  -> ERRO: Falha ao processar o arquivo {nome_arquivo}. Exceção: {e}")

            print("-" * 60)

        print("\n[+] Todos os testes foram processados! Verifique os arquivos 'output_*.py' gerados.")