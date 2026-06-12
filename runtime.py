def ligar(namedevice):
    """Ativa o dispositivo e retorna 1"""
    print(f"{namedevice} ligado!")
    return 1

def desligar(namedevice):
    """Desativa o dispositivo e retorna 0"""
    print(f"{namedevice} desligado!")
    return 0

def verificar(namedevice):
    """
    Verifica o estado do dispositivo.
    Aqui fazemos uma simulação simples (retornando 1), 
    mas você pode expandir a lógica se desejar.
    """
    # Como o pseudocódigo do enunciado mostra duas possibilidades de print 
    # dependendo do estado, printamos uma mensagem padrão de ativo.
    print(f"{namedevice} esta ligado.")
    return 1

def alerta(namedevice, msg, var=None):
    """
    Envia um alerta para o dispositivo.
    Aceita a mensagem simples ou a mensagem concatenada com uma variável.
    """
    print(f"{namedevice} recebeu o alerta:\n")
    if var is not None:
        # Atende ao requisito de separar por espaço em branco: msg + " " + var
        print(f"{msg} {var}")
    else:
        print(msg)