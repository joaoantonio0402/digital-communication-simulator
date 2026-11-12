# Simulador de Comunicação Digital — Fase 1

## Arquitetura

O fluxo implementado é:

1. A mensagem ASCII é convertida em bits, com oito bits por caractere.
2. O codificador de linha produz níveis `-1/+1`. No NRZ há um nível por bit;
   no Manchester há dois níveis por bit (`0 -> +1,-1` e `1 -> -1,+1`).
3. Cada nível é representado por um *chip bit* (`-1 -> 0`, `+1 -> 1`).
   Esses bits são agrupados e modulados em símbolos complexos.
4. O canal adiciona ruído AWGN aos símbolos modulados.
5. O receptor demodula, remove o preenchimento final usado para completar o
   último símbolo, reconstrói os níveis e decodifica a linha.

Esse desenho evita tratar uma forma de onda de linha como se fosse diretamente
um símbolo QPSK/QAM. A codificação de linha continua sendo observável e
testável, enquanto a modulação trabalha sobre uma sequência binária bem
definida.

As constelações são normalizadas para potência média unitária: BPSK usa
`±1`, QPSK usa `(±1 ± j)/sqrt(2)` e 16-QAM usa amplitudes
`±1, ±3` divididas por `sqrt(10)`. O AWGN usa
`P_ruído = P_sinal / 10^(SNR_dB/10)`; para ruído complexo, essa potência é
dividida igualmente entre as partes real e imaginária.

## Execução

```text
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

O valor de seed é opcional e torna a transmissão reproduzível. Esta fase não
inclui experimentos, varreduras de SNR, estatística agregada ou gráficos.

## Testes

```text
pytest -q
```
