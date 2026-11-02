# LocaFácil

Sistema desktop para Windows de gestão de aluguéis de equipamentos, feito com Python, CustomTkinter e SQLite.

## Recursos

- Cadastro de equipamentos com patrimônio e importação de listas (`.xlsx`, `.xls`, `.ods`, `.csv`, `.xml`, `.json`, `.docx` e outros)
- Contratos com vários itens e controle de estoque por período
- Histórico de contratos, com edição e exclusão
- Dados salvos localmente, com backup automático

## Como executar

```bash
pip install -r requirements.txt
python main.py
```

## Testes e compilação

```bash
pip install -r requirements-dev.txt
python -m pytest
pyinstaller --noconfirm main.spec
```

## Licença

Todos os direitos reservados. Veja [LICENSE](LICENSE).
