# Simulador de Comunicação Digital

Projeto acadêmico para avaliação experimental de codificação de linha,
modulação digital, canais ruidosos, taxa de erro de bits e eficiência espectral.
O repositório inclui o simulador interativo, o plano de experimentos, os
resultados brutos, gráficos BER × Eb/N0 e testes automatizados.

## Arquitetura

O fluxo implementado é:

1. A mensagem ASCII é convertida em bits, com oito bits por caractere.
2. O codificador de linha produz níveis `-1/+1`. No NRZ há um nível por bit;
   no Manchester há dois níveis por bit (`0 -> +1,-1` e `1 -> -1,+1`).
3. Cada nível é representado por um *chip bit* (`-1 -> 0`, `+1 -> 1`).
   Esses bits são agrupados e modulados em símbolos complexos.
4. O canal adiciona AWGN ou AWGN com ruído em rajadas aos símbolos modulados.
5. O receptor demodula, remove o preenchimento final usado para completar o
   último símbolo, reconstrói os níveis e decodifica a linha.

Esse desenho evita tratar uma forma de onda de linha como se fosse diretamente
um símbolo QPSK/QAM. A codificação de linha continua sendo observável e
testável, enquanto a modulação trabalha sobre uma sequência binária bem
definida.

### Codificação de linha x correção de erros

Codificação de linha define como os bits são representados fisicamente no
enlace, por exemplo, com os níveis e transições usados por NRZ e Manchester.
Ela pode melhorar propriedades do sinal, como sincronização, mas não adiciona
redundância para recuperar bits corrompidos.

Codificação de correção de erros adiciona bits redundantes à mensagem para que
o receptor detecte e, conforme o código utilizado, corrija erros causados pelo
canal. Este simulador implementa codificação de linha, mas ainda não implementa
um código de correção de erros.

As constelações são normalizadas para potência média unitária: BPSK usa
`±1`, QPSK usa `(±1 ± j)/sqrt(2)` e 16-QAM usa amplitudes
`±1, ±3` divididas por `sqrt(10)`. O AWGN usa
`P_ruído = P_sinal / 10^(SNR_dB/10)`; para ruído complexo, essa potência é
dividida igualmente entre as partes real e imaginária.

## Equipe

- Integrante 1: preencher nome e responsabilidade.
- Integrante 2: preencher nome e responsabilidade.

## Execução do simulador interativo

```text
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

O valor de seed é opcional e torna a transmissão reproduzível. O resultado
também informa os índices dos bits incorretos, usando indexação iniciada em
zero.

### Cenários de canal

O cenário AWGN adiciona ruído gaussiano complexo com potência definida pela
SNR informada. O cenário `Ruído em rajadas` mantém esse ruído de fundo e
adiciona ruído de potência configurada em intervalos consecutivos. Cada amostra
inicia uma rajada com probabilidade de 1%, cada rajada dura até 8 amostras e
tem SNR de 0 dB. A mesma seed torna os resultados reproduzíveis.

### Experimentos e gráficos

O plano oficial utiliza 9 valores de Eb/N0: 0, 2, 4, 6, 8, 10, 12, 14 e
16 dB. Cada combinação usa 100.000 bits de informação e 5 repetições
independentes. Os parâmetros são mantidos equivalentes nas comparações.

Execute os experimentos completos:

```text
python -m src.experiments
```

Eles salvam os resultados brutos em `results/raw_results.csv`, os resumos em
`results/summary.csv` e a configuração em `results/config.json`. Para gerar as
curvas BER × Eb/N0 com intervalos de confiança de 95%:

```text
python -m src.plot_results
```

São gerados quatro gráficos em `results/plots/`, combinando cada codificação
de linha com cada cenário de canal. Cada curva identifica a modulação e a
faixa sombreada representa o intervalo de confiança das repetições.

Na escala vertical logarítmica, uma BER igual a zero é representada no piso
`10^-12` apenas como convenção gráfica. A geração também pode ser executada
diretamente:

```text
python src\experiments.py --quick
python src\plot_results.py --summary results\summary.csv --out results\plots
```

O modo `--quick` é destinado a testes rápidos e utiliza 10.000 bits e
2 repetições.

## Eficiência espectral

A eficiência espectral nominal considera sinalização ideal, sem roll-off e
sem código de correção de erros. Manchester transmite dois chips por bit,
portanto reduz pela metade a eficiência da mesma modulação em NRZ.

| Codificação | Modulação | Bits por símbolo | Eficiência nominal (bits/s/Hz) |
|---|---|---:|---:|
| NRZ | BPSK | 1 | 1 |
| NRZ | QPSK | 2 | 2 |
| NRZ | 16-QAM | 4 | 4 |
| Manchester | BPSK | 1/2 | 0,5 |
| Manchester | QPSK | 1 | 1 |
| Manchester | 16-QAM | 2 | 2 |

O 16-QAM oferece a maior eficiência espectral, mas exige maior relação
Eb/N0 para atingir uma BER baixa. BPSK é a opção mais robusta, enquanto
QPSK oferece um compromisso intermediário: dobra a eficiência do BPSK sem
utilizar a menor robustez do 16-QAM.

## Resultados experimentais

Os resultados oficiais, com 100.000 bits por ensaio e 5 repetições, estão
registrados em [`results/raw_results.csv`](./results/raw_results.csv),
[`results/summary.csv`](./results/summary.csv) e
[`results/config.json`](./results/config.json). Os gráficos correspondentes
estão em [`results/plots`](./results/plots).

Observações:

- No canal AWGN, a BER diminui de forma consistente à medida que Eb/N0
  aumenta. BPSK e QPSK atingem BER nula nas maiores razões simuladas.
- O 16-QAM mantém maior BER no conjunto de Eb/N0 testado porque seus pontos
  da constelação estão mais próximos uns dos outros.
- O ruído em rajadas cria um patamar residual de BER em valores altos de
  Eb/N0. Isso ocorre porque o ruído intenso continua afetando intervalos
  consecutivos mesmo com o ruído de fundo reduzido.
- Para cada modulação, o canal com rajadas apresenta BER maior que o AWGN
  isolado nas condições analisadas.
- Manchester sofre uma penalidade de eficiência espectral, pois envia duas
  transições/chips por bit. Seu uso é mais adequado quando sincronização por
  transição é mais importante que maximizar a taxa nominal.

## Testes

```text
pytest -q
```

Os testes cobrem conversão ASCII, codificações de linha, modulações,
reprodutibilidade dos canais, métricas, experimentos, geração de resumos e
gráficos.
