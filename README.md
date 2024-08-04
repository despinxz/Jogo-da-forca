# Jogo da forca
Este repositório contém o script de um jogo da forca implementado em Python utilizando sockets TCP.

A disputa é feita entre dois jogadores. Cada um escolhe a palavra que seu adversário terá que adivinhar. O primeiro a acertar a palavra vence. 

## Como executar
Para executar o jogo, é necessário que o servidor seja iniciado. Execute o seguinte comando no terminal:

    python servidor_script.py

Após a inicialização do servidor, os dois jogadores podem se conectar, executando o comando:

    python cliente_script.py
