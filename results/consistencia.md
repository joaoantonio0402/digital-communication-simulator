# Teste de consistência

Mensagem enviada (46 caracteres, 368 bits): `Redes de Computadores - UNISINOS - Trabalho II`
Seed: 2026. Rajadas: {'burst_probability': 0.01, 'burst_length': 8, 'burst_snr_db': 0.0}.

| Cenário | Codificação | Modulação | Bits errados | BER | Caracteres afetados | Mensagem recuperada |
|---|---|---|---:|---:|---:|---|
| Canal ideal (sem ruído) | NRZ | BPSK | 0 | 0.0000 | 0 | sim |
| Canal ideal (sem ruído) | NRZ | QPSK | 0 | 0.0000 | 0 | sim |
| Canal ideal (sem ruído) | NRZ | 16-QAM | 0 | 0.0000 | 0 | sim |
| Canal ideal (sem ruído) | Manchester | BPSK | 0 | 0.0000 | 0 | sim |
| Canal ideal (sem ruído) | Manchester | QPSK | 0 | 0.0000 | 0 | sim |
| Canal ideal (sem ruído) | Manchester | 16-QAM | 0 | 0.0000 | 0 | sim |
| AWGN, Eb/N0 = 30 dB | NRZ | BPSK | 0 | 0.0000 | 0 | sim |
| AWGN, Eb/N0 = 30 dB | NRZ | QPSK | 0 | 0.0000 | 0 | sim |
| AWGN, Eb/N0 = 30 dB | NRZ | 16-QAM | 0 | 0.0000 | 0 | sim |
| AWGN, Eb/N0 = 30 dB | Manchester | BPSK | 0 | 0.0000 | 0 | sim |
| AWGN, Eb/N0 = 30 dB | Manchester | QPSK | 0 | 0.0000 | 0 | sim |
| AWGN, Eb/N0 = 30 dB | Manchester | 16-QAM | 0 | 0.0000 | 0 | sim |
| AWGN, Eb/N0 = 6 dB | NRZ | BPSK | 0 | 0.0000 | 0 | sim |
| AWGN, Eb/N0 = 6 dB | NRZ | QPSK | 2 | 0.0054 | 2 | NÃO |
| AWGN, Eb/N0 = 6 dB | NRZ | 16-QAM | 15 | 0.0408 | 12 | NÃO |
| AWGN, Eb/N0 = 6 dB | Manchester | BPSK | 10 | 0.0272 | 10 | NÃO |
| AWGN, Eb/N0 = 6 dB | Manchester | QPSK | 11 | 0.0299 | 10 | NÃO |
| AWGN, Eb/N0 = 6 dB | Manchester | 16-QAM | 24 | 0.0652 | 18 | NÃO |
| Rajadas, Eb/N0 = 16 dB | NRZ | BPSK | 1 | 0.0027 | 1 | NÃO |
| Rajadas, Eb/N0 = 16 dB | NRZ | QPSK | 5 | 0.0136 | 3 | NÃO |
| Rajadas, Eb/N0 = 16 dB | NRZ | 16-QAM | 0 | 0.0000 | 0 | sim |
| Rajadas, Eb/N0 = 16 dB | Manchester | BPSK | 3 | 0.0082 | 3 | NÃO |
| Rajadas, Eb/N0 = 16 dB | Manchester | QPSK | 3 | 0.0082 | 3 | NÃO |
| Rajadas, Eb/N0 = 16 dB | Manchester | 16-QAM | 7 | 0.0190 | 4 | NÃO |

## Exemplos de divergência

- AWGN, Eb/N0 = 6 dB, NRZ + 16-QAM: recebido `R'deS de Aomtutadorus!-`?NISINOS -!T?abalho!IM`; primeiros bits incorretos (base 0): [9, 14, 34, 78, 101, 155, 175, 185, 192, 196]
- Rajadas, Eb/N0 = 16 dB, NRZ + BPSK: recebido `Redes de Computadores - UNISINOS - Trab!lho II`; primeiros bits incorretos (base 0): [313]

## Interpretação

- Em canal ideal e em AWGN com Eb/N0 alto, a mensagem é recuperada sem erros: o pipeline (ASCII, linha, modulação, demodulação, decodificação) é consistente.
- Em Eb/N0 baixo surgem bits errados; o ruído aproxima os símbolos dos limites de decisão, e o 16-QAM erra mais por ter pontos mais próximos.
- No canal com rajadas, mesmo com Eb/N0 alto podem restar erros: as rajadas de ruído forte não diminuem quando o ruído de fundo diminui (piso de erro).
- Uma mensagem curta tem poucos bits, então a contagem de erros é só ilustrativa; as estatísticas confiáveis vêm do experimento com 100.000 bits e 5 repetições.
