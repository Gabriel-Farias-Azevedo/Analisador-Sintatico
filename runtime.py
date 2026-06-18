# Ativa o dispositivo simulado e retorna 1
def ligar(namedevice):
    print(f"{namedevice} ligado!")
    return 1

# Desativa o dispositivo simulado e retorna 0
def desligar(namedevice):
    print(f"{namedevice} desligado!")
    return 0

# Verifica e retorna o estado atual do dispositivo
def verificar(namedevice):
    print(f"{namedevice} esta ligado.")
    return 1

# Exibe uma mensagem de alerta para o dispositivo com suporte a variáveis
def alerta(namedevice, msg, var=None):
    print(f"{namedevice} recebeu o alerta:\n")
    if var is not None:
        print(f"{msg} {var}")
    else:
        print(msg)