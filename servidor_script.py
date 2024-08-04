import random
import socket
import threading
import time


# Classe que armazena informações sobre cada jogador
class Jogador:
    # Construtor
    def __init__(self, socket):
        self.socket = socket  # Próprio socket
        self.socket_oponente = None  # Socket do oponente
        self.palavra = ""  # Palavra a ser adivinhada
        self.username = ""  # Username
        self.tentativas = 6  # Tentativas restantes
        self.letras_tentadas = []  # Lista de letras tentadas
        self.palavras_tentadas = []  # Lista de palavras tentadas
        self.palavra_incompleta = ""  # Palavra a ser completada (inicialmente apenas ___)

    # Setters
    def set_username(self, username):
        self.username = username

    def set_palavra(self, palavra):
        self.palavra = palavra
        self.palavra_incompleta = "_" * len(palavra)

    def set_socket_oponente(self, socket_oponente):
        self.socket_oponente = socket_oponente

    # Getters
    def get_username(self):
        return self.username

    def get_palavra(self):
        return self.palavra

    # Função que verifica se a tentativa foi correta ou falha e retorna a mensagem apropriada para o cliente
    def ver_tentativa(self, tent):
        resposta = ""

        # Se a tentativa não for alfabética
        if not tent.isalpha():
            resposta = "tent;invalido"

        # Se a tentativa for apenas uma letra
        elif len(tent) == 1:

            # Se a letra já tiver sido tentada
            if tent in self.letras_tentadas:
                resposta = "tent;letra_repetida"

            # Caso contrário
            else:
                self.letras_tentadas.append(tent)
                # Se a letra estiver na palavra
                if tent in self.palavra:
                    self.palavra_incompleta = revela_letra(self.palavra_incompleta, self.palavra, tent)

                    if "_" not in self.palavra_incompleta:
                        resposta = "tent;vitoria"
                    else:
                        resposta = "tent;correto"

                # Se a letra não estiver na palavra
                elif tent not in self.palavra:
                    self.tentativas -= 1
                    resposta = "tent;incorreto"

        # Se a tentativa for uma palavra inteira
        elif len(tent) == len(self.palavra):

            # Se a palavra já tiver sido tentada
            if tent in self.palavras_tentadas:
                resposta = "tent;palavra_repetida"

            # Caso contrário
            else:
                self.palavras_tentadas.append(tent)

                # Se a palavra estiver correta
                if tent == self.palavra:
                    self.palavra_incompleta = tent
                    resposta = "tent;vitoria"

                # Caso contrário
                else:
                    self.tentativas -= 1
                    resposta = "tent;incorreto"

        # Se a tentativa não tiver uma letra nem o mesmo tamanho da palavra
        else:
            resposta = "tent;invalido"

        # Se o número de tentativas do jogador chegar a 0, encerra o jogo
        if self.tentativas == 0:
            resposta = "tent;fim_tentativas"

        return resposta

    # Função que trata as tentativas do jogador
    def trata_cliente(self):
        while True:
            # Recebe mensagem
            data = self.socket.recv(1024).decode("utf-8")

            if data:
                tipo_msg, msg = data.split(";", 1)

                # Caso o jogador ainda tenha tentativas restantes
                if self.tentativas > 0:

                    # Caso a mensagem seja uma tentativa
                    if tipo_msg == "tent":
                        resposta = self.ver_tentativa(msg)

                        # Se o jogador tiver vencido, notifica o oponente da sua derrota
                        if resposta == "tent;vitoria":
                            self.socket_oponente.send("tent;derrota".encode("utf-8"))

                        # Se o jogador não tiver mais tentativas, notifica o oponente da sua vitória
                        if resposta == "tent;fim_tentativas":
                            self.socket_oponente.send("tent;vitoria_tentativas".encode("utf-8"))

                        # Envia resposta ao jogador
                        self.socket.send(resposta.encode("utf-8"))

                        # Recebe confirmação
                        tent_confirmacao = self.socket.recv(1024).decode("utf-8")

                        # Exibe erro caso confirmação não seja recebida
                        if tent_confirmacao != "recebida":
                            print("Erro: tentativa não foi processada")

                    # Caso a mensagem seja um pedido de dica
                    elif tipo_msg == "dica":
                        l = primeira_letra(self.palavra_incompleta, self.palavra)
                        self.palavra_incompleta = revela_letra(self.palavra_incompleta, self.palavra, l)
                        self.letras_tentadas.append(l)

                        self.socket.send(f"{l}".encode("utf-8"))

                    # Envia string com a palavra incompleta
                    self.socket.send(f"palavra;{self.palavra_incompleta}".encode("utf-8"))


# Função para revelar uma letra da palavra
def revela_letra(palavra, palavra_completa, letra):
    p_lista = list(palavra)

    for index, letra_aux in enumerate(palavra_completa):
        if letra_aux == letra:
            p_lista[index] = letra

    palavra = "".join(p_lista)
    return palavra


# Função para pegar primeira letra não revelada da palavra (usada no contexto de dar uma dica
def primeira_letra(palavra, palavra_completa):
    for index, letra_aux in enumerate(palavra):
        if letra_aux == "_":
            letra = palavra_completa[index]
            return letra


# Função para obter as informações do jogador antes do início do jogo
def get_jogador_info(jogador, tema, palavra):
    msg = jogador.socket.recv(1024).decode("utf-8")

    tipo_msg, msg = msg.split(";", 1)

    # Mensagem para nome de usuário
    if tipo_msg == "username":
        jogador.set_username(msg)

    # Envia tema para o jogador
    jogador.socket.send(f"tema;{tema}".encode("utf-8"))

    # Recebe palavra escolhida pelo jogador para o seu oponente
    msg = jogador.socket.recv(1024).decode("utf-8")

    tipo_msg, msg = msg.split(";", 1)

    if tipo_msg == "palavra":
        palavra[0] = msg

    # Envia mensagem para aguardar a conexão do outro jogador
    jogador.socket.send("status;aguarde_oponente".encode("utf-8"))


# Função para sortear um tema
def sorteia_tema():
    temas = ["Animais", "Frutas", "Objetos", "Países", "Profissões", "Comidas"]
    random_int = random.randint(0, len(temas) - 1)
    return temas[random_int]


# Função para enviar mensagens para ambos os jogadores
def broadcast_msg(j1, j2, msg):
    j1.socket.send(msg.encode("utf-8"))
    j2.socket.send(msg.encode("utf-8"))


# Main
if __name__ == "__main__":
    # Cria servidor
    host = socket.gethostname()
    port = 55551
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Conecta aos clientes
    try:
        server.bind((host, port))
        server.listen(2)  # Somente 2 jogadores podem conectar-se
    except:
        print("Não foi possível iniciar o servidor.")
        exit()

    print("Aguardando jogadores...")

    # Sorteia o tema da partida
    tema = sorteia_tema()

    # Contador de conexões
    num_conexoes = 0

    # Cria conexões, cria objetos jogadores e prepara o início do jogo
    while num_conexoes < 2:
        # Conecta cliente
        cliente_socket, cliente_address = server.accept()
        num_conexoes += 1

        # Lida com jogador 1
        if num_conexoes == 1:
            j1 = Jogador(cliente_socket)
            j1_palavra = [None] * 1

            # Inicia thread para conseguir informações do jogador 1 antes do início do jogo
            j1_info = threading.Thread(target=get_jogador_info,
                                       args=(j1, tema, j1_palavra))
            j1_info.start()

        # Lida com jogador 2 e inicia jogo
        else:
            j2 = Jogador(cliente_socket)
            j2_palavra = [None] * 1

            # Inicia thread para conseguir informações do jogador 2 antes do início do jogo
            j2_info = threading.Thread(target=get_jogador_info,
                                       args=(j2, tema, j2_palavra))
            j2_info.start()

            # Termina threads
            j1_info.join()
            j2_info.join()

            # Seta a palavra de cada jogador
            j1.set_palavra(j2_palavra[0])
            j2.set_palavra(j1_palavra[0])

            # Seta socket do oponente de cada jogador
            j1.set_socket_oponente(j2.socket)
            j2.set_socket_oponente(j1.socket)

            # Envia nome do oponente para cada jogador
            j1.socket.send(f"oponente;{j2.get_username()}".encode("utf-8"))
            j2.socket.send(f"oponente;{j1.get_username()}".encode("utf-8"))

            # Aguarda confirmação de que os nomes foram recebidos
            j1_nome_pronto = j1.socket.recv(1024).decode("utf-8")
            j2_nome_pronto = j2.socket.recv(1024).decode("utf-8")

            # Envia erro e encerra o programa caso os nomes não tenham sido recebidos
            if j1_nome_pronto != "nome_pronto" or j2_nome_pronto != "nome_pronto":
                print("Erro: os clientes não receberam o nome de seus oponentes.")
                time.sleep(3)
                exit()

            # Envia tamanho da palavra de cada jogador
            j1.socket.send(f"tamanho;{len(j1.get_palavra())}".encode("utf-8"))
            j2.socket.send(f"tamanho;{len(j2.get_palavra())}".encode("utf-8"))

            # Aguarda confirmação de que tamanhos foram recebidos
            j1_tamanho_pronto = j1.socket.recv(1024).decode("utf-8")
            j2_tamanho_pronto = j2.socket.recv(1024).decode("utf-8")

            # Envia erro e encerra programa caso tamanhos não tenham sido recebidos
            if j1_tamanho_pronto != "tamanho_pronto" or j2_tamanho_pronto != "tamanho_pronto":
                print("Erro: os clientes não receberam o tamanho de suas palavras.")
                time.sleep(3)
                exit()

            # Notifica que o jogo está pronto após ambos os jogadores terem se conectado
            broadcast_msg(j1, j2, "status;jogo_pronto")

            # Aguarda confirmação de que ambos os jogadores estão prontos
            j1_jogo_pronto = j1.socket.recv(1024).decode("utf-8")
            j2_jogo_pronto = j2.socket.recv(1024).decode("utf-8")

            # Envia erro e encerra programa caso jogadores não consigam iniciar o jogo
            if j1_jogo_pronto != "jogo_pronto" or j2_jogo_pronto != "jogo_pronto":
                print("Erro: os clientes não conseguiram iniciar o jogo.")
                time.sleep(3)
                exit()

            # Notifica o início do jogo
            broadcast_msg(j1, j2, "status;inicia_jogo")

    # Inicia o jogo para ambos os jogadores
    threading.Thread(target=j1.trata_cliente).start()
    threading.Thread(target=j2.trata_cliente).start()
