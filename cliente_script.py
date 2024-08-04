import socket
import threading
import time

from os import system, name


# Função que desenha o homem da forca
def homem_forca(tentativas):
    estagios = [
        # estagio final: cabeça, torso, dois braços, duas pernas
        """
           --------
           |      |
           |      O
           |     \\|/
           |      |
           |     / \\
           -
        """,
        # cabeça, torso, dois braços, uma perna
        """
           --------
           |      |
           |      O
           |     \\|/
           |      |
           |     / 
           -
        """,
        # cabeça, torso, dois braços
        """
           --------
           |      |
           |      O
           |     \\|/
           |      |
           |      
           -
        """,
        # cabeça, torso, um braço
        """
           --------
           |      |
           |      O
           |     \\|
           |      |
           |     
           -
        """,
        # cabeça, torso
        """
           --------
           |      |
           |      O
           |      |
           |      |
           |     
           -
        """,
        # cabeça
        """
           --------
           |      |
           |      O
           |    
           |      
           |     
           -
        """,
        # estágio inicial: vazio
        """
           --------
           |      |
           |      
           |    
           |      
           |     
           -
        """,
        # estágio de morte
        """
                   --------
                   |      |
                   |      X
                   |     \\|/
                   |      |
                   |     / \\
                   -
                """

    ]
    return estagios[tentativas]


# Função para lidar com uma tentativa
def tentativa(cliente, tentativas, palavra_incompleta):
    print(homem_forca(tentativas))
    print(palavra_incompleta)

    tent = input("Tentativa: ").upper()
    cliente.send(f"tent;{tent}".encode("utf-8"))


# Função para verificar se o jogador tem direito a dicas (se mais da metade da palavra já tiver sido revelada, NÃO TEM)
def verifica_dica(palavra):
    cont_letra = 0

    for letra in palavra:
        if letra != "_":
            cont_letra += 1

    if cont_letra >= len(palavra) / 2:
        return False
    else:
        return True


# Main
if __name__ == "__main__":

    # Cria cliente
    host = socket.gethostname()
    port = 55551
    cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    tentativas = 6

    # Conecta ao servidor
    try:
        cliente.connect((host, port))
    except:
        print("Não foi possível se conectar ao servidor.")

    # Inicia jogo
    print("Bem-vindo ao jogo da forca!")
    print(homem_forca(0))

    # Pede nome de usuário
    username = input("Digite seu username: ")
    cliente.send(f"username;{username}".encode("utf-8"))
    print("Conectado!")

    # Inicia troca de mensagens
    while True:
        msg = cliente.recv(1024).decode("utf-8")

        tipo_msg, msg = msg.split(";", 1)

        # Primeira mensagem recebida: tema
        # Resposta: palavra do oponente
        if tipo_msg == "tema":
            print(f"Tema da partida: {msg}")
            palavra_oponente = input("Escolha a palavra do seu oponente "
                                     "(apenas uma palavra, sem espaços ou hífens): ").upper()
            cliente.send(f"palavra;{palavra_oponente}".encode("utf-8"))

        # Segunda mensagem recebida: nome do oponente
        # Resposta: confirmação do recebimento do nome
        elif tipo_msg == "oponente":
            nome_oponente = msg
            cliente.send("nome_pronto".encode("utf-8"))

        # Terceira mensagem recebida: tamanho da palavra
        # Resposta: confirmação do recebimento do tamanho
        elif tipo_msg == "tamanho":
            len_palavra = int(msg)
            palavra_incompleta = "_" * len_palavra
            cliente.send("tamanho_pronto".encode("utf-8"))

        # Mensagens do tipo status
        elif tipo_msg == "status":

            # Mensagem caso oponente ainda não tenha se conectado
            if msg == "aguarde_oponente":
                print("Aguardando oponente...")

            # Caso o servidor tenha indicado que o jogo está pronto para ser iniciado, envia confirmação para o servidor
            elif msg == "jogo_pronto":
                print("JOGO INICIADO!")
                print(f"{username} vs. {nome_oponente}")
                cliente.send("jogo_pronto".encode("utf-8"))

            # Caso o servidor tenha enviado mensagem para iniciar o jogo, roda a primeira tentativa do jogador
            if msg == "inicia_jogo":
                print("Partida iniciando...")
                time.sleep(3)
                print(homem_forca(tentativas))
                print(palavra_incompleta)
                tent = input("Tentativa: ").upper()
                cliente.send(f"tent;{tent}".encode("utf-8"))

        # Mensagem que recebe o atual estado da palavra sendo adivinhada
        elif tipo_msg == "palavra":
            palavra_incompleta = msg

        # Mensagens de resposta do servidor às tentativas
        elif tipo_msg == "tent":

            # Envia confirmação ao servidor
            cliente.send("recebida".encode("utf-8"))

            # Recebe palavra incompleta
            tipo_msg, palavra_incompleta = cliente.recv(1024).decode("utf-8").split(";", 1)

            # Jogador acertou a letra/palavra
            if msg == "correto":
                print("Você acertou!")
                time.sleep(2)

            # Jogador errou a letra/palavra
            elif msg == "incorreto":
                tentativas -= 1
                print("Errou!")
                time.sleep(1)

                # Caso o jogador tenha direito a dicas, pergunta se ele quer
                if verifica_dica(palavra_incompleta):
                    dica = input("Você gostaria que uma das letras fosse revelada? (S/N): ").upper()

                    # Caso o jogador queira uma dica
                    if dica == "S":
                        # Envia pedido de dica ao servidor
                        cliente.send("dica;dica".encode("utf-8"))

                        # Recebe letra revelada
                        letra = cliente.recv(1024).decode("utf-8")
                        print(f"Uma letra foi revelada: {letra}")
                        time.sleep(2)

                        # Recebe palavra incompleta novamente
                        tipo_msg, palavra_incompleta = cliente.recv(1024).decode("utf-8").split(";", 1)

                    # Caso a resposta seja inválida
                    elif dica != "N":
                        print("Resposta inválida. Iniciando outra tentativa...")
                        time.sleep(2)

            # Jogador descobriu a palavra
            elif msg == "vitoria":
                print("Você ganhou!")
                time.sleep(3)
                exit()

            # Oponente descobriu a palavra primeiro
            elif msg == "derrota":
                print("Seu oponente acertou a palavra antes de você. Você perdeu.")
                time.sleep(3)
                exit()

            # Jogador já usou todas suas tentativas
            elif msg == "fim_tentativas":
                print("Errou!")
                time.sleep(0.5)
                print("Você esgotou suas tentativas! O homem foi enforcado!")
                time.sleep(0.5)
                print(homem_forca(7))
                time.sleep(1)
                exit()

            # Oponente já usou todas suas tentativas
            elif msg == "vitoria_tentativas":
                print("Seu oponente não conseguiu acertar a palavra. Você venceu!")
                time.sleep(3)
                exit()

            elif msg == "letra_repetida":
                print("Você já tentou essa letra!")
                time.sleep(2)

            elif msg == "palavra_repetida":
                print("Você já tentou essa palavra!")
                time.sleep(2)

            elif msg == "invalido":
                print("Você pode apenas inserir caracteres alfanuméricos ou palavras com o tamanho certo.")
                time.sleep(2)

            # Roda outra tentativa
            tentativa(cliente, tentativas, palavra_incompleta)





