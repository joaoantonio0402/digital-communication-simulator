| Codificação | Modulação | Eficiência (bits/s/Hz) | BER AWGN @ 6 dB | BER AWGN @ 10 dB | Eb/N0 p/ BER ≤ 1e-03 (dB) | BER rajadas @ 16 dB | Uso mais adequado |
|---|---|---|---|---|---|---|---|
| NRZ | BPSK | 1.0 | 2.2e-03 | 4.0e-06 | 6.6 | 6.3e-03 | Enlaces ruidosos ou de baixa energia: é a mais robusta, mas usa a banda de forma pouco eficiente. |
| NRZ | QPSK | 2.0 | 2.4e-03 | 4.0e-06 | 6.7 | 1.3e-02 | Melhor compromisso geral: dobra a eficiência do BPSK com a mesma BER para o mesmo Eb/N0. |
| NRZ | 16-QAM | 4.0 | 2.8e-02 | 1.8e-03 | 10.5 | 2.2e-02 | Enlaces limpos (Eb/N0 alto) em que a banda é escassa: maior taxa, menor robustez. |
| Manchester | BPSK | 0.5 | 2.3e-02 | 7.2e-04 | 9.7 | 6.5e-03 | Quando o sincronismo por transição pesa mais que banda e energia: custa 3 dB e metade da eficiência. |
| Manchester | QPSK | 1.0 | 2.3e-02 | 8.8e-04 | 9.9 | 1.3e-02 | Mesmo caso do Manchester + BPSK, com o dobro da eficiência. |
| Manchester | 16-QAM | 2.0 | 5.2e-02 | 1.1e-02 | 13.0 | 1.6e-02 | Sincronismo por transição em enlace limpo; ainda assim exige muito mais Eb/N0 que o NRZ. |
